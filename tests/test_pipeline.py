import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from xcard_automation.core.pipeline import RunConfig, run_pipeline
from xcard_automation.core.validator import load_datacard


def test_default_pipeline_generates_a_valid_genesis_core_card(
    dataset_dir: Path, complete_answers: dict[str, object], tmp_path: Path
) -> None:
    answers_path = tmp_path / "answers.json"
    answers_path.write_text(json.dumps(complete_answers), encoding="utf-8")
    output_root = tmp_path / "runs"

    assert run_pipeline(RunConfig(dataset_dir, "core", output_root, answers_path)) == 0

    card = next(
        (output_root / dataset_dir.name / "automation_output").glob(
            "genesis_datacard_*.md"
        )
    )
    text = card.read_text(encoding="utf-8")
    assert "Datacard for Sample Materials Dataset" in text
    assert "## Discovery" in text
    metadata, _ = load_datacard(card)
    assert metadata["discoverability"]["datacard"]["template_version"] == "1.2"
    assert metadata["discoverability"]["identification"]["name"] == "Sample Materials Dataset"
    assert metadata["supports_interoperability"] == "Yes"
    assert metadata["interoperability"]["data_structure"]["features"] == [
        {"name": "sample"},
        {"name": "value"},
    ]
    assert metadata["reusability"]["integrity"]["checksum_available"] == "Yes"
    report = json.loads(
        (output_root / dataset_dir.name / "validation_output" / "validation_report.json").read_text()
    )
    assert report["ok"]
    assert (output_root / dataset_dir.name / "validation_output" / card.name).exists()


def test_default_pipeline_writes_checksums_before_validation(
    dataset_dir: Path, complete_answers: dict[str, object], tmp_path: Path
) -> None:
    answers = complete_answers | {
        "license.spdx_id": "MIT",
        "license.name": "MIT License",
        "dates.data_collection_start": "2026-01-01",
        "dates.data_collection_end": "2026-01-02",
    }
    answers_path = tmp_path / "answers.json"
    answers_path.write_text(json.dumps(answers), encoding="utf-8")
    output_root = tmp_path / "runs"

    assert run_pipeline(RunConfig(dataset_dir, "core", output_root, answers_path)) == 0
    assert (output_root / dataset_dir.name / "automation_output" / "checksums.sha256").exists()
    card = next((output_root / dataset_dir.name / "automation_output").glob("genesis_datacard_*.md"))
    metadata, _ = load_datacard(card)
    assert metadata["supports_ai_usability"] == "No"


def test_pipeline_normalizes_uppercase_dataset_slug_for_canonical_filename(
    dataset_dir: Path, complete_answers: dict[str, object], tmp_path: Path
) -> None:
    dataset_dir = dataset_dir.rename(tmp_path / "FAIR_SRP")
    answers_path = tmp_path / "answers.json"
    answers_path.write_text(json.dumps(complete_answers), encoding="utf-8")
    output_root = tmp_path / "runs"

    assert run_pipeline(RunConfig(dataset_dir, "core", output_root, answers_path)) == 0

    run_dir = output_root / "FAIR_SRP"
    card = run_dir / "automation_output" / "genesis_datacard_fair_srp.md"
    assert card.exists()
    assert json.loads((run_dir / "validation_output" / "validation_report.json").read_text())["ok"]
    assert (run_dir / "validation_output" / card.name).exists()


def test_default_pipeline_rejects_unimplemented_profiles(
    dataset_dir: Path, tmp_path: Path
) -> None:
    with pytest.raises(ValueError, match="Profile 'ai_ready' is not supported"):
        run_pipeline(RunConfig(dataset_dir, "ai_ready", tmp_path / "runs"))


def test_pipeline_renders_approved_title_and_authors(
    dataset_dir: Path, complete_answers: dict[str, object], tmp_path: Path
) -> None:
    answers_path = tmp_path / "answers.json"
    answers_path.write_text(
        json.dumps(
            complete_answers
            | {
                "identification": {"name": "Sample Materials Benchmark"},
                "authors": [{"given_name": "Grace", "family_name": "Hopper"}],
                "citation": {
                    "preferred_citation": {
                        "author": "Grace Hopper",
                        "title": "Sample Materials Benchmark",
                        "year": "2026",
                        "publisher": "Example Laboratory",
                        "doi": "10.1234/example",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    assert run_pipeline(RunConfig(dataset_dir, "core", tmp_path / "runs", answers_path)) == 0

    metadata, _ = load_datacard(
        next((tmp_path / "runs" / dataset_dir.name / "automation_output").glob("genesis_datacard_*.md"))
    )
    assert metadata["discoverability"]["identification"]["name"] == "Sample Materials Benchmark"
    assert metadata["discoverability"]["authors"] == [
        {"person": {"given_name": "Grace", "family_name": "Hopper", "email": None}}
    ]
    assert metadata["reusability"]["citation"]["preferred_citation"]["doi"] == "10.1234/example"


def test_pipeline_records_cited_llm_assistance(
    dataset_dir: Path, complete_answers: dict[str, object], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    answers_path = tmp_path / "answers.json"
    answers_path.write_text(json.dumps(complete_answers), encoding="utf-8")
    evidence = {
        "agent": {"name": "Test Model", "version": "1.0.0"},
        "candidates": [
            {
                "path": "description.summary",
                "value": "LLM-cited summary",
                "confidence": 0.9,
                "citations": [{"source": "README.md", "start_line": 1, "end_line": 1}],
            }
        ],
        "proposals": [
            {
                "path": "identification.name",
                "value": "Sample Materials Benchmark",
                "confidence": 0.9,
                "citations": [{"source": "README.md", "start_line": 1, "end_line": 1}],
            }
        ],
    }
    monkeypatch.setattr(
        "xcard_automation.core.llm_crawl.subprocess.run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout=json.dumps(evidence), stderr=""),
    )

    output_root = tmp_path / "runs"
    assert run_pipeline(
        RunConfig(dataset_dir, "core", output_root, answers_path, llm_command=["agent"])
    ) == 0
    metadata, _ = load_datacard(
        next((output_root / dataset_dir.name / "automation_output").glob("genesis_datacard_*.md"))
    )
    assert metadata["discoverability"]["dataset_description"]["dataset_summary"] == "LLM-cited summary"
    assert metadata["discoverability"]["identification"]["name"] == "Sample Materials Dataset"
    assert metadata["discoverability"]["datacard"]["created_by"][-1]["creator"]["ai_model"]["name"] == "Test Model"
    assert json.loads(
        (output_root / dataset_dir.name / "automation_output" / "llm_proposals.json").read_text()
    )[0]["value"] == "Sample Materials Benchmark"
