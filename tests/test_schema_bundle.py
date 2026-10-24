import json
from pathlib import Path
from shutil import copy2, copytree

import pytest

from xcard_automation.core.pipeline import RunConfig, run_pipeline
from xcard_automation.main import main
from xcard_automation.core.schema_bundle import (
    collect_bundle_answers,
    default_bundle_path,
    load_bundle,
    project_model,
    render_bundle,
    validate_model,
)


def test_local_bundle_uses_its_own_paths_enums_and_template(tmp_path: Path) -> None:
    (tmp_path / "bundle.yaml").write_text(
        "id: alternate\nversion: '9'\ntemplate: card.j2\nlinkml_schema: schema.yaml\nroot_class: Card\nmapping: mapping.yaml\n",
        encoding="utf-8",
    )
    (tmp_path / "schema.yaml").write_text(
        "classes:\n  Card:\n    attributes:\n      label: {required: true, range: Label}\nenums:\n  Label:\n    permissible_values: {'Approved': {}}\n",
        encoding="utf-8",
    )
    (tmp_path / "mapping.yaml").write_text(
        "fields:\n  - target: label\n    value: {source: metadata.state, lookup: {ready: Approved}}\n",
        encoding="utf-8",
    )
    (tmp_path / "card.j2").write_text("# {{ model.label }}\n", encoding="utf-8")

    bundle = load_bundle(tmp_path)
    model = project_model(bundle, {"metadata": {"state": "ready"}})

    assert model == {"label": "Approved"}
    assert validate_model(bundle, model) == []
    assert render_bundle(bundle, model) == "# Approved\n"


def test_bundle_prompts_for_missing_answer_mappings(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "bundle.yaml").write_text(
        "id: prompt\nversion: '1'\ntemplate: card.j2\nlinkml_schema: schema.yaml\n"
        "root_class: Card\nmapping: mapping.yaml\n",
        encoding="utf-8",
    )
    (tmp_path / "schema.yaml").write_text("classes: {Card: {}}\n", encoding="utf-8")
    (tmp_path / "mapping.yaml").write_text(
        "fields:\n  - target: label\n    prompt: Label\n"
        "    value: {first: [{source: answers.label}, {constant: fallback}]}\n",
        encoding="utf-8",
    )
    (tmp_path / "card.j2").write_text("{{ model.label }}\n", encoding="utf-8")
    bundle = load_bundle(tmp_path)

    class Answer:
        def ask(self) -> str:
            return "entered label"

    monkeypatch.setattr("xcard_automation.core.schema_bundle.sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("xcard_automation.core.schema_bundle.questionary.text", lambda *_: Answer())

    assert collect_bundle_answers(bundle, [("label", "required value is missing")], {}) == {
        "label": "entered label"
    }


def test_bundle_requires_a_declared_ontology_asset(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    copytree(default_bundle_path(), bundle_dir)
    copy2(
        load_bundle(default_bundle_path()).schema_path,
        bundle_dir / "schema.yaml",
    )
    manifest = (bundle_dir / "bundle.yaml").read_text(encoding="utf-8")
    (bundle_dir / "bundle.yaml").write_text(
        manifest.replace(
            "../../../../xcard-evaluation/bundles/genesis_datacard/1.2/schema/genesis_datacard.yaml",
            "schema.yaml",
        ),
        encoding="utf-8",
    )
    (bundle_dir / "ontology.yaml").unlink()

    with pytest.raises(ValueError, match="Bundle ontology"):
        load_bundle(bundle_dir)


def test_pipeline_runs_an_unrelated_local_bundle(
    dataset_dir: Path, tmp_path: Path, capsys
) -> None:
    bundle = tmp_path / "portable"
    bundle.mkdir()
    (bundle / "bundle.yaml").write_text(
        "id: portable\nversion: '3'\ntemplate: card.j2\nlinkml_schema: schema.yaml\n"
        "root_class: Card\nmapping: mapping.yaml\n"
        "output_filename: portable_{{ context.dataset.slug }}.md\n",
        encoding="utf-8",
    )
    (bundle / "schema.yaml").write_text(
        "classes:\n  Card:\n    attributes:\n      title: {required: true, range: string}\n"
        "      published: {required: true, range: date}\n"
        "      status: {required: true, range: PublicationStatus}\n"
        "enums:\n  PublicationStatus:\n    permissible_values: {Approved: {}}\n",
        encoding="utf-8",
    )
    (bundle / "mapping.yaml").write_text(
        "fields:\n  - target: title\n    value: {source: answers.title}\n"
        "  - target: published\n    value: {source: answers.published}\n"
        "  - target: status\n    value: {constant: Approved}\n",
        encoding="utf-8",
    )
    (bundle / "card.j2").write_text(
        "---\n{{ model | tojson(indent=2) }}\n---\n# {{ model.title }}\n",
        encoding="utf-8",
    )
    answers = tmp_path / "answers.json"
    answers.write_text(
        json.dumps({"title": "Portable card", "published": "2026-10-23"}),
        encoding="utf-8",
    )
    output_root = tmp_path / "output"

    assert run_pipeline(
        RunConfig(dataset_dir, "portable", output_root, answers, schema_bundle=bundle)
    ) == 0

    card = output_root / dataset_dir.name / "validation_output" / "portable_sample_dataset.md"
    assert card.read_text(encoding="utf-8").endswith("# Portable card\n")
    assert main(["evaluate", str(card), "--schema-bundle", str(bundle)]) == 0
    assert capsys.readouterr().out == "OK\n"
    normalized = json.loads(
        (output_root / dataset_dir.name / "automation_output" / "normalized_metadata.json").read_text()
    )
    assert normalized == {
        "title": "Portable card",
        "published": "2026-10-23",
        "status": "Approved",
    }
