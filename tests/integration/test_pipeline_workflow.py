import json
from pathlib import Path

import pytest

from xcard_automation.core.pipeline import RunConfig, run_pipeline
from xcard_automation.core.validator import load_datacard


@pytest.mark.integration
def test_pipeline_persists_a_valid_workflow_with_harness_answers(
    dataset_dir: Path,
    complete_answers: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Exercise the pipeline's filesystem and answer-collection boundaries."""
    collected: dict[str, object] = {}

    def collect_answers(
        metadata: dict[str, object],
        answers: dict[str, object],
        missing_fields: list[str],
    ) -> dict[str, object]:
        collected.update(
            metadata=metadata,
            answers=answers,
            missing_fields=missing_fields,
        )
        return complete_answers

    monkeypatch.setattr("xcard_automation.core.pipeline.collect_answers", collect_answers)
    answers_path = tmp_path / "agent-answers.json"
    answers_path.write_text("{}", encoding="utf-8")
    output_root = tmp_path / "integration-runs"
    project_name = "isolated-workflow"

    assert run_pipeline(
        RunConfig(dataset_dir, "core", output_root, answers_path, project_name=project_name)
    ) == 0

    run_dir = output_root / project_name
    persisted_answers = json.loads((run_dir / "input" / "answers.yaml").read_text())
    normalized_metadata = json.loads(
        (run_dir / "automation_output" / "normalized_metadata.json").read_text()
    )
    datacard = next((run_dir / "automation_output").glob("genesis_datacard_*.md"))
    card_metadata, _ = load_datacard(datacard)

    assert collected["answers"] == {}
    assert "identification.project" in collected["missing_fields"]
    assert persisted_answers == complete_answers
    assert card_metadata == normalized_metadata
    assert (run_dir / "validation_output" / datacard.name).read_text() == datacard.read_text()
    assert json.loads((run_dir / "validation_output" / "validation_report.json").read_text())["ok"]
    assert not (dataset_dir / "automation_output").exists()


@pytest.mark.integration
def test_pipeline_persists_unresolved_fields_without_a_datacard(
    dataset_dir: Path, tmp_path: Path
) -> None:
    output_root = tmp_path / "integration-runs"

    assert run_pipeline(RunConfig(dataset_dir, "core", output_root)) == 1

    run_dir = output_root / dataset_dir.name
    unresolved = json.loads(
        (run_dir / "automation_output" / "unresolved_fields.json").read_text()
    )
    assert "identification.project" in unresolved["missing_fields"]
    assert (run_dir / "input" / "introspection.json").exists()
    assert not list((run_dir / "automation_output").glob("genesis_datacard_*.md"))
