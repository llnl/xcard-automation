from pathlib import Path

from xcard_automation.core.introspect import inspect_dataset
from xcard_automation.core.mapper import build_metadata
from xcard_automation.core.validator import validate_metadata


def test_build_metadata_produces_a_valid_core_datacard(
    dataset_dir: Path, complete_answers: dict[str, object]
) -> None:
    metadata = build_metadata(
        dataset_dir,
        "core",
        inspect_dataset(dataset_dir),
        complete_answers,
    )

    result = validate_metadata(metadata)

    assert metadata["identification"]["name"] == "Sample Materials Dataset"
    assert metadata["dataset_type"] == "ND"
    assert result.ok


def test_validator_reports_invalid_enums_and_template_placeholders() -> None:
    metadata = {
        "datacard": {"profile": "core"},
        "categorization": {"science_domain": "unknown"},
        "security": {"classification": "TOP_SECRET"},
    }

    result = validate_metadata(metadata, raw_text="Name: ${identification.name}")
    codes = {finding.code for finding in result.findings}

    assert {"MISSING_REQUIRED", "BAD_ENUM", "UNRESOLVED_PLACEHOLDER"} <= codes
