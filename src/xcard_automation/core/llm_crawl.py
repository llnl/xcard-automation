"""Bounded repository-crawl support for external LLM agents."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess
from typing import Any

import yaml

from .utils import get_path, is_missing, set_path

MAX_FILES = 500
MAX_FILE_BYTES = 1_000_000
MAX_TOTAL_BYTES = 10_000_000
TEXT_SUFFIXES = {".md", ".rst", ".txt", ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".csv", ".py", ".ipynb"}
EXCLUDED_PARTS = {".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist", ".cache", "automation_output", "validation_output"}
SECRET_NAMES = {".env", ".netrc", "id_rsa", "id_ed25519"}
SECRET_RE = re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*[^\s]+")


@dataclass(frozen=True)
class LLMRun:
    answers: dict[str, Any]
    evidence: dict[str, Any]
    resolution: dict[str, Any]
    proposals: list[dict[str, Any]]
    creator: dict[str, Any] | None


def default_skill_path() -> Path:
    return Path(__file__).resolve().parents[1] / "skills" / "repository-crawl" / "SKILL.md"


def build_crawl_manifest(dataset_dir: Path) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    total_bytes = 0
    for path in sorted(dataset_dir.rglob("*")):
        if not path.is_file() or any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        relative = path.relative_to(dataset_dir).as_posix()
        if path.name in SECRET_NAMES or path.suffix.lower() in {".key", ".pem", ".p12"}:
            manifest.append({"path": relative, "status": "excluded_secret"})
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            manifest.append({"path": relative, "status": "excluded_type"})
            continue
        size = path.stat().st_size
        if size > MAX_FILE_BYTES or total_bytes + size > MAX_TOTAL_BYTES or len(manifest) >= MAX_FILES:
            manifest.append({"path": relative, "status": "excluded_limit"})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if SECRET_RE.search(text):
            manifest.append({"path": relative, "status": "excluded_secret"})
            continue
        total_bytes += size
        manifest.append({"path": relative, "status": "included", "bytes": size})
    return manifest


def enrich_answers(
    command: list[str] | None,
    dataset_dir: Path,
    bundle_root: Path,
    policy_path: Path | None,
    answers: dict[str, Any],
    introspection: dict[str, Any],
    request_path: Path,
) -> LLMRun:
    if not command:
        return LLMRun(answers, {}, {"accepted": [], "rejected": []}, [], None)
    manifest = build_crawl_manifest(dataset_dir)
    request = {
        "version": "1.0",
        "dataset_dir": str(dataset_dir),
        "bundle": str(bundle_root),
        "skill": default_skill_path().read_text(encoding="utf-8"),
        "manifest": manifest,
        "introspection": introspection,
        "web_access": "public_https",
    }
    request_path.write_text(json.dumps(request, indent=2), encoding="utf-8")
    try:
        completed = subprocess.run(
            command,
            input=json.dumps(request),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
            check=False,
        )
        if completed.returncode:
            raise ValueError(completed.stderr.strip() or "agent exited unsuccessfully")
        evidence = json.loads(completed.stdout)
        if not isinstance(evidence, dict):
            raise ValueError("agent output must be a JSON object")
    except (OSError, subprocess.TimeoutExpired, ValueError, json.JSONDecodeError) as error:
        return LLMRun(answers, {"error": str(error)}, {"accepted": [], "rejected": [{"reason": str(error)}]}, [], None)
    safe_paths = _safe_paths(policy_path)
    review_paths = _review_paths(policy_path)
    allowed_sources = {
        item["path"] for item in manifest if item.get("status") == "included"
    }
    resolved = dict(answers)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for candidate in evidence.get("candidates", []):
        reason = _candidate_error(candidate, safe_paths, allowed_sources)
        if reason:
            rejected.append({"candidate": candidate, "reason": reason})
            continue
        path = candidate["path"]
        if not is_missing(_answer_value(resolved, path)):
            rejected.append({"candidate": candidate, "reason": "explicit answer takes precedence"})
            continue
        set_path(resolved, path, candidate["value"])
        accepted.append(candidate)
    proposals: list[dict[str, Any]] = []
    for proposal in evidence.get("proposals", []):
        reason = _candidate_error(proposal, review_paths, allowed_sources)
        if reason:
            rejected.append({"proposal": proposal, "reason": reason})
            continue
        proposals.append(proposal)
    creator = evidence.get("agent") if accepted and isinstance(evidence.get("agent"), dict) else None
    return LLMRun(resolved, evidence, {"accepted": accepted, "rejected": rejected}, proposals, creator)


def _safe_paths(policy_path: Path | None) -> set[str]:
    return _policy_paths(policy_path, "llm_safe_paths")


def _review_paths(policy_path: Path | None) -> set[str]:
    return _policy_paths(policy_path, "llm_review_paths")


def _policy_paths(policy_path: Path | None, key: str) -> set[str]:
    if not policy_path or not policy_path.is_file():
        return set()
    data = yaml.safe_load(policy_path.read_text(encoding="utf-8")) or {}
    return set(data.get(key, []))


def _candidate_error(
    candidate: Any, safe_paths: set[str], allowed_sources: set[str]
) -> str | None:
    if not isinstance(candidate, dict):
        return "candidate must be an object"
    if candidate.get("path") not in safe_paths:
        return "path is not approved for LLM enrichment"
    if "value" not in candidate:
        return "candidate value is required"
    if not isinstance(candidate.get("confidence"), (int, float)) or candidate["confidence"] < 0.8:
        return "confidence must be at least 0.80"
    citations = candidate.get("citations")
    if not isinstance(citations, list) or not citations:
        return "at least one citation is required"
    if not all(
        isinstance(citation, dict)
        and isinstance(citation.get("source"), str)
        and (
            citation["source"] in allowed_sources
            or citation["source"].startswith("https://")
        )
        for citation in citations
    ):
        return "citations must reference an included file or public HTTPS URL"
    return None


def _answer_value(answers: dict[str, Any], path: str) -> Any:
    return answers.get(path, get_path(answers, path))
