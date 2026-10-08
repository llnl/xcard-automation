import json
import subprocess
import sys
from pathlib import Path

from xcard_automation.core.pipeline import RunConfig, run_pipeline


def test_core_pipeline_writes_a_valid_markdown_datacard(
    dataset_dir: Path, complete_answers: dict[str, object], tmp_path: Path
) -> None:
    answers_path = tmp_path / "answers.json"
    answers_path.write_text(json.dumps(complete_answers), encoding="utf-8")
    output_root = tmp_path / "runs"

    assert run_pipeline(RunConfig(dataset_dir, "core", output_root, answers_path)) == 0

    card = next(
        (output_root / dataset_dir.name / "validation_output").glob(
            "genesis_datacard_*.md"
        )
    )
    text = card.read_text(encoding="utf-8")
    assert "\n# Datacard for Sample Materials Dataset\n" in text
    assert "\n| Aspect | Status |\n" in text


def test_ai_ready_pipeline_writes_checksum_manifest(
    dataset_dir: Path, complete_answers: dict[str, object], tmp_path: Path
) -> None:
    answers = complete_answers | {
        "license.spdx_id": "MIT",
        "license.name": "MIT License",
        "dates.data_collection_start": "2026-01-01",
        "dates.data_collection_end": "2026-01-02",
        "ai_usage.ai_ready": "conditional",
        "ai_usage.training_use_allowed": "true",
        "ai_usage.inference_use_allowed": "conditional",
        "ai_usage.evaluation_use_allowed": "true",
        "ai_usage.human_review_required": True,
        "data_quality.completeness": "Complete",
        "data_quality.known_issues": "No known issues",
        "data_quality.validation_methods": "Checked",
        "semantic_layer.schema_url": "https://example.org/schema",
    }
    answers_path = tmp_path / "answers.json"
    answers_path.write_text(json.dumps(answers), encoding="utf-8")
    output_root = tmp_path / "runs"

    assert run_pipeline(RunConfig(dataset_dir, "ai_ready", output_root, answers_path)) == 0
    assert (output_root / dataset_dir.name / "automation_output" / "checksums.sha256").exists()


def test_module_exit_code_reflects_pipeline_failure(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "xcard_automation",
            "generate",
            str(tmp_path / "missing_dataset"),
            "--profile",
            "core",
            "--output-root",
            str(tmp_path / "runs"),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
