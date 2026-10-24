from dataclasses import dataclass
from datetime import date
from shutil import copy2
from pathlib import Path
from typing import Any

from jinja2 import TemplateError

from .artifacts import prepare_run_dirs, write_run_inputs
from .evaluation import rendered_card_findings, validate_card
from .introspect import build_checksum_manifest, inspect_dataset
from .llm_crawl import LLMRun, enrich_answers
from .schema_bundle import (
    collect_bundle_answers,
    default_bundle_path,
    load_bundle,
    project_model,
    render_bundle,
    render_output_filename,
    validate_model,
)
from .utils import load_yaml_file, snake_case, write_json_file


@dataclass
class RunConfig:
    dataset_dir: Path
    profile: str
    output_root: Path
    answers_path: Path | None = None
    resume: bool = False
    schema_bundle: Path = default_bundle_path()
    project_name: str | None = None
    llm_command: list[str] | None = None


def run_pipeline(config: RunConfig) -> int:
    dataset_dir = config.dataset_dir.resolve()
    introspection = inspect_dataset(dataset_dir)
    dataset_slug = introspection["dataset_slug"]
    run_dirs = prepare_run_dirs(config.output_root, config.project_name or dataset_slug)
    answers_path = config.answers_path or (run_dirs["input"] / "answers.yaml")
    answers = load_yaml_file(answers_path, {})
    if not isinstance(answers, dict):
        raise ValueError("Answers file must contain a mapping")
    bundle = load_bundle(config.schema_bundle)
    profiles = bundle.manifest.get("profiles")
    if profiles is not None and config.profile not in profiles:
        raise ValueError(
            f"Profile {config.profile!r} is not supported by {bundle.id}@{bundle.version}"
        )
    checksum_info = build_checksum_manifest(dataset_dir, run_dirs["automation_output"] / "checksums.sha256")
    llm_run = enrich_answers(
        config.llm_command,
        dataset_dir,
        bundle.root,
        bundle.automation_policy_path,
        answers,
        introspection,
        run_dirs["input"] / "llm_crawl_request.json",
    )
    answers = llm_run.answers
    write_json_file(run_dirs["automation_output"] / "llm_evidence.json", llm_run.evidence)
    write_json_file(run_dirs["automation_output"] / "llm_resolution.json", llm_run.resolution)
    write_json_file(run_dirs["automation_output"] / "llm_proposals.json", llm_run.proposals)
    context = _bundle_context(dataset_dir, introspection, answers, config.profile, checksum_info, llm_run)

    source_manifest = {
        "dataset_dir": str(dataset_dir),
        "profile": config.profile,
        "schema_bundle": str(bundle.root),
        "schema_id": bundle.id,
        "schema_version": bundle.version,
        "template_path": str(bundle.template_path),
        "linkml_schema": str(bundle.schema_path),
        "ontology": str(bundle.ontology_path) if bundle.ontology_path else None,
        "output_root": str(run_dirs["root"]),
        "project_name": config.project_name,
        "resume": config.resume,
        "llm_command": config.llm_command,
    }
    write_run_inputs(run_dirs, source_manifest, introspection, answers)
    write_json_file(
        run_dirs["input"] / "ontology_summary.json",
        {
            "schema_id": bundle.id,
            "linkml_schema": source_manifest["linkml_schema"],
            "ontology": source_manifest["ontology"],
            "root_class": bundle.manifest["root_class"],
        },
    )
    rendered_metadata = project_model(bundle, context)
    bundle_findings = validate_model(bundle, rendered_metadata)
    if bundle_findings:
        answers = collect_bundle_answers(bundle, bundle_findings, answers)
        context = _bundle_context(dataset_dir, introspection, answers, config.profile, checksum_info, llm_run)
        rendered_metadata = project_model(bundle, context)
        bundle_findings = validate_model(bundle, rendered_metadata)
        write_run_inputs(run_dirs, source_manifest, introspection, answers)
    write_json_file(run_dirs["automation_output"] / "normalized_metadata.json", rendered_metadata)
    findings = [
        {"code": "SCHEMA_INVALID", "field": path, "severity": "error", "message": message}
        for path, message in bundle_findings
    ]
    if findings:
        _write_validation_report(run_dirs["validation_output"], findings)
        return 1
    try:
        filename = render_output_filename(bundle, context)
        rendered_card = render_bundle(bundle, rendered_metadata)
        render_findings = rendered_card_findings(rendered_card, filename)
        if render_findings:
            _write_validation_report(run_dirs["validation_output"], render_findings)
            return 1
        datacard_path = run_dirs["automation_output"] / filename
        datacard_path.write_text(rendered_card, encoding="utf-8")
    except (OSError, TemplateError, ValueError) as error:
        _write_validation_report(
            run_dirs["validation_output"],
            [
                {
                    "code": "RENDER_FAILED",
                    "field": "(document)",
                    "severity": "error",
                    "message": str(error),
                }
            ],
        )
        return 1
    findings = validate_card(datacard_path, bundle)
    if findings:
        _write_validation_report(run_dirs["validation_output"], findings)
        return 1
    _write_validation_report(run_dirs["validation_output"], [])
    copy2(datacard_path, run_dirs["validation_output"] / datacard_path.name)
    return 0


def _write_validation_report(validation_dir: Path, findings: list[dict[str, str]]) -> None:
    report = {"ok": not findings, "findings": findings}
    write_json_file(validation_dir / "validation_report.json", report)
    (validation_dir / "validation_summary.md").write_text(
        _render_validation_summary(report), encoding="utf-8"
    )


def _render_validation_summary(report: dict[str, Any]) -> str:
    lines = ["# Validation Summary", "", "Status: PASS" if report["ok"] else "Status: FAIL", ""]
    if not report["findings"]:
        return "\n".join([*lines, "No findings.", ""])
    lines.extend(
        f"- [{finding['severity']}] {finding['code']} `{finding['field']}`: {finding['message']}"
        for finding in report["findings"]
    )
    return "\n".join([*lines, ""])


def _bundle_context(
    dataset_dir: Path,
    introspection: dict[str, Any],
    answers: dict[str, Any],
    profile: str,
    checksum_info: dict[str, Any],
    llm_run: LLMRun,
) -> dict[str, Any]:
    return {
        "dataset": {
            "path": str(dataset_dir),
            "slug": snake_case(introspection["dataset_slug"]),
            "name": dataset_dir.name.replace("_", " ").title(),
        },
        "introspection": introspection,
        "answers": answers,
        "profile": profile,
        "checksums": checksum_info,
        "interoperability": _interoperability_context(introspection),
        "llm": {"created_by": _created_by(llm_run.creator)},
        "run": {"date": date.today().isoformat()},
    }


def _created_by(agent: dict[str, Any] | None) -> list[dict[str, Any]]:
    creators = [
        {
            "contribution_date": date.today().isoformat(),
            "description": "Generated by xcard-automation",
            "creator": {
                "software": {
                    "name": "xcard-automation",
                    "version": "0.3.0",
                    "identifier": {"type": "local", "value": "xcard-automation"},
                    "relationship": "used_to_create",
                }
            },
        }
    ]
    if agent and isinstance(agent.get("name"), str):
        creators.append(
            {
                "contribution_date": date.today().isoformat(),
                "description": "Repository evidence extraction",
                "creator": {
                    "ai_model": {
                        "name": agent["name"],
                        "version": str(agent.get("version", "0.0.0")),
                        "accessed_date": date.today().isoformat(),
                        "identifier": {"type": "local", "value": agent["name"]},
                        "relationship": "used_to_analyze",
                    }
                },
            }
        )
    return creators


def _interoperability_context(introspection: dict[str, Any]) -> dict[str, list[str]]:
    formats = introspection.get("formats") or ["Unknown"]
    modalities: list[str] = []
    if any(value in {"CSV", "TSV", "JSON", "YAML", "Parquet", "Arrow"} for value in formats):
        modalities.append("tabular")
    if any(value in {"PNG", "JPEG", "TIFF"} for value in formats):
        modalities.append("image")
    if any(value in {"Text", "Markdown"} for value in formats):
        modalities.append("text")
    if any(value in {"HDF5", "NetCDF4"} for value in formats):
        modalities.append("time-series")
    sample_columns = introspection.get("sample_columns", {})
    features = next(iter(sample_columns.values()), [])
    return {
        "formats": formats,
        "modalities": modalities or ["other"],
        "features": features or ["not_documented"],
    }
