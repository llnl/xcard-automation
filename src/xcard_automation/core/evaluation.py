"""Validate rendered cards through xcard-evaluation when available."""

from pathlib import Path
from typing import Any

from xcard_evaluation import SchemaRequest, read_card_text, validate
from xcard_evaluation.seams import CardError, finding_from_error

from .schema_bundle import SchemaBundle, validate_model
from .validator import load_datacard


def rendered_card_findings(
    content: str, filename: str
) -> list[dict[str, str | None]]:
    """Return parsing findings for a rendered Markdown card."""
    try:
        read_card_text(content, filename)
    except CardError as error:
        return [_finding_dict(finding_from_error(error))]
    return []


def validate_card(
    path: Path, bundle: SchemaBundle
) -> list[dict[str, str | None]]:
    """Validate a card with its canonical evaluator or local bundle schema."""
    if bundle.id == "genesis_datacard" and bundle.version == "1.2":
        try:
            result = validate(
                path,
                bundles=bundle.schema_path.parents[3],
                request=SchemaRequest(schema_id="genesis_datacard", version="1.2"),
            )
        except CardError as error:
            return [_finding_dict(finding_from_error(error))]
        return [_finding_dict(finding) for finding in result.findings]
    model, _ = load_datacard(path)
    return [
        {
            "code": "SCHEMA_INVALID",
            "field": field,
            "severity": "error",
            "message": message,
        }
        for field, message in validate_model(bundle, model)
    ]


def _finding_dict(finding: Any) -> dict[str, str | None]:
    return {
        "code": finding.code,
        "field": finding.path or "(document)",
        "severity": str(finding.severity),
        "message": finding.message,
    }
