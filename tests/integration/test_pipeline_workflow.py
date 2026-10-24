import json
from pathlib import Path

import pytest

from xcard_automation.core.pipeline import RunConfig, run_pipeline
from xcard_automation.core.validator import load_datacard


@pytest.mark.integration
def test_pipeline_persists_a_valid_genesis_card_with_harness_answers(
    dataset_dir: Path,
    complete_answers: dict[str, object],
    tmp_path: Path,
) -> None:
    """Exercise the pipeline's filesystem and answer persistence boundaries."""
    answers_path = tmp_path / "agent-answers.json"
    answers_path.write_text(json.dumps(complete_answers), encoding="utf-8")
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

    assert persisted_answers == complete_answers
    assert card_metadata == normalized_metadata
    assert json.loads(
        (run_dir / "validation_output" / "validation_report.json").read_text()
    )["ok"]
    assert (run_dir / "validation_output" / datacard.name).exists()
    assert not (dataset_dir / "automation_output").exists()


@pytest.mark.integration
def test_pipeline_persists_unresolved_fields_without_a_datacard(
    dataset_dir: Path, tmp_path: Path
) -> None:
    output_root = tmp_path / "integration-runs"
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "bundle.yaml").write_text(
        "id: test\nversion: '1'\ntemplate: card.j2\nlinkml_schema: schema.yaml\n"
        "root_class: Card\nmapping: mapping.yaml\nprofiles: [core]\n",
        encoding="utf-8",
    )
    (bundle / "schema.yaml").write_text(
        "classes:\n  Card:\n    attributes:\n      label: {required: true, range: string}\n",
        encoding="utf-8",
    )
    (bundle / "mapping.yaml").write_text(
        "fields:\n  - target: label\n    prompt: Label\n    value: {source: answers.label}\n",
        encoding="utf-8",
    )
    (bundle / "card.j2").write_text("# {{ model.label }}\n", encoding="utf-8")

    assert run_pipeline(RunConfig(dataset_dir, "core", output_root, schema_bundle=bundle)) == 1

    run_dir = output_root / dataset_dir.name
    report = json.loads(
        (run_dir / "validation_output" / "validation_report.json").read_text()
    )
    assert report["findings"][0]["field"] == "label"
    assert (run_dir / "input" / "introspection.json").exists()
    assert not list((run_dir / "automation_output").glob("genesis_datacard_*.md"))


@pytest.mark.integration
def test_pipeline_reports_template_rendering_failures(
    dataset_dir: Path, tmp_path: Path
) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "bundle.yaml").write_text(
        "id: test\nversion: '1'\ntemplate: card.j2\nlinkml_schema: schema.yaml\n"
        "root_class: Card\nmapping: mapping.yaml\n",
        encoding="utf-8",
    )
    (bundle / "schema.yaml").write_text(
        "classes:\n  Card:\n    attributes:\n      label: {required: true, range: string}\n",
        encoding="utf-8",
    )
    (bundle / "mapping.yaml").write_text(
        "fields:\n  - target: label\n    value: {constant: ready}\n",
        encoding="utf-8",
    )
    (bundle / "card.j2").write_text("{{ model.missing }}\n", encoding="utf-8")

    assert run_pipeline(RunConfig(dataset_dir, "core", tmp_path / "out", schema_bundle=bundle)) == 1
    report = json.loads(
        (tmp_path / "out" / dataset_dir.name / "validation_output" / "validation_report.json").read_text()
    )
    assert report["findings"][0]["code"] == "RENDER_FAILED"
    assert not list((tmp_path / "out" / dataset_dir.name / "automation_output").glob("*.md"))
