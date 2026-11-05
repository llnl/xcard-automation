import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
from typing import Any

import yaml
from .contract import ENUMS, SCIENCE_DOMAINS, required_fields
from .ontology import FIELD_TO_ONTOLOGY_ENUM, alignment_report
from .utils import get_path, has_placeholders, is_missing, snake_case


@dataclass
class Finding:
    code: str
    field: str
    severity: str = "error"
    message: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "field": self.field,
            "severity": self.severity,
            "message": self.message,
        }


@dataclass
class ValidationResult:
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(item.severity == "error" for item in self.findings)

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "findings": [item.as_dict() for item in self.findings]}


def load_datacard(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"^---\s*$", text, maxsplit=2, flags=re.MULTILINE)
    if len(parts) < 3:
        raise ValueError(f"{path} does not contain standard YAML frontmatter")
    data = yaml.safe_load(parts[1]) if parts[1].strip() else {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} frontmatter is not a mapping")
    return data, text


def validate_metadata(metadata: dict[str, Any], raw_text: str | None = None) -> ValidationResult:
    if "discoverability" in metadata:
        return _validate_v1_2_metadata(metadata, raw_text)
    findings: list[Finding] = []
    profile = metadata.get("datacard", {}).get("profile", "core")
    for path in required_fields(profile, metadata):
        value = get_path(metadata, path)
        if is_missing(value):
            findings.append(Finding("MISSING_REQUIRED", path, "error", "required value is missing"))

    for path, allowed in ENUMS.items():
        value = get_path(metadata, path)
        if is_missing(value):
            continue
        if value not in allowed:
            findings.append(Finding("BAD_ENUM", path, "error", f"expected one of {sorted(allowed)}; got {value!r}"))

    science_domain = get_path(metadata, "categorization.science_domain")
    if science_domain and science_domain not in SCIENCE_DOMAINS:
        findings.append(Finding("BAD_ENUM", "categorization.science_domain", "error", f"unknown science domain {science_domain!r}"))

    for path in [
        "datacard.created_date",
        "datacard.updated_date",
        "dates.data_collection_start",
        "dates.data_collection_end",
        "dates.issued",
        "dates.modified",
        "security.last_reviewed_date",
    ]:
        value = get_path(metadata, path)
        if value in (None, "", "not_applicable"):
            continue
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value)):
            findings.append(Finding("BAD_FORMAT", path, "error", "expected YYYY-MM-DD"))

    expected_filename = f"genesis_datacard_{snake_case(metadata.get('identification', {}).get('name', ''))}.md"
    actual_filename = get_path(metadata, "datacard.filename", "")
    if actual_filename and actual_filename != expected_filename:
        findings.append(Finding("INCONSISTENT", "datacard.filename", "warn", f"expected {expected_filename}, got {actual_filename}"))

    state = get_path(metadata, "workflow.state")
    release_status = metadata.get("release_status")
    alignment = {
        "raw": {"draft"},
        "processing": {"draft"},
        "qa": {"draft"},
        "analysis": {"draft"},
        "review": {"under_review", "approved"},
        "embargo": {"approved", "published"},
        "published": {"approved", "published"},
        "archived": {"deprecated", "published"},
    }
    if state in alignment and release_status and release_status not in alignment[state]:
        findings.append(Finding("INCONSISTENT", "workflow.state", "warn", f"workflow.state={state} is unusual for release_status={release_status}"))

    if raw_text is not None and has_placeholders(raw_text):
        findings.append(Finding("UNRESOLVED_PLACEHOLDER", "(document)", "error", "rendered output still contains template placeholders"))

    ontology_alignment = alignment_report(metadata)
    for path, details in ontology_alignment["checked_fields"].items():
        if not details["matches_ontology"]:
            findings.append(
                Finding(
                    "ONTOLOGY_ENUM_MISMATCH",
                    path,
                    "warn",
                    f"value {details['value']!r} does not align with ontology enum {FIELD_TO_ONTOLOGY_ENUM[path]}",
                )
            )

    return ValidationResult(findings)


def _validate_v1_2_metadata(metadata: dict[str, Any], raw_text: str | None) -> ValidationResult:
    findings: list[Finding] = []
    required = [
        "supports_discoverability",
        "supports_accessibility",
        "supports_interoperability",
        "supports_reusability",
        "supports_governed_use",
        "supports_ai_usability",
        "discoverability.datacard.template_version",
        "discoverability.datacard.datacard_version",
        "discoverability.datacard.filename",
        "discoverability.datacard.change_log[0].change_date",
        "discoverability.datacard.change_log[0].data_card_version",
        "discoverability.datacard.created_by[0].contribution_date",
        "discoverability.identification.name",
        "discoverability.identification.version",
        "interoperability.data_structure.formats",
    ]
    for path in required:
        if is_missing(get_path(metadata, path)):
            findings.append(Finding("MISSING_REQUIRED", path, "error", "required value is missing"))
    if get_path(metadata, "discoverability.datacard.template_version") != "1.2":
        findings.append(Finding("BAD_TEMPLATE_VERSION", "discoverability.datacard.template_version", "error", "expected 1.2"))
    capabilities = [
        "supports_discoverability",
        "supports_accessibility",
        "supports_interoperability",
        "supports_reusability",
        "supports_governed_use",
        "supports_ai_usability",
    ]
    for path in capabilities:
        if get_path(metadata, path) not in {"Yes", "No"}:
            findings.append(Finding("BAD_ENUM", path, "error", "expected Yes or No"))
    if get_path(metadata, "supports_ai_usability") == "Yes":
        for use in ("training", "inference", "evaluation"):
            status = get_path(metadata, f"ai_usability.ai_usage.{use}_use_status")
            if status not in {"Yes", "No", "Conditional"}:
                findings.append(Finding("BAD_ENUM", f"ai_usability.ai_usage.{use}_use_status", "error", "expected Yes, No, or Conditional"))
            conditions = get_path(metadata, f"ai_usability.ai_usage.{use}_use_conditions")
            if status == "Conditional" and conditions in (None, "", "not_applicable"):
                findings.append(Finding("MISSING_REQUIRED", f"ai_usability.ai_usage.{use}_use_conditions", "error", "required when status is Conditional"))
    if raw_text is not None and has_placeholders(raw_text):
        findings.append(Finding("UNRESOLVED_PLACEHOLDER", "(document)", "error", "rendered output still contains template placeholders"))
    return ValidationResult(findings)


def validate_file(path: Path) -> ValidationResult:
    metadata, raw_text = load_datacard(path)
    return validate_metadata(metadata, raw_text)


def render_validation_summary(result: ValidationResult) -> str:
    lines = ["# Validation Summary", ""]
    lines.extend(("Status: PASS" if result.ok else "Status: FAIL", ""))
    if not result.findings:
        lines.append("No findings.")
        return "\n".join(lines) + "\n"
    lines.extend(f"- [{f.severity}] {f.code} `{f.field}`: {f.message}" for f in result.findings)
    return "\n".join(lines) + "\n"
