import json
import subprocess
import sys
from pathlib import Path

import pytest
from pytest import MonkeyPatch

from xcard_automation.main import main
from xcard_automation.cli import configure, evaluate, run
from xcard_automation.core.pipeline import RunConfig
from xcard_automation.core.validator import Finding, ValidationResult


def test_inspect_reads_paths_from_config(dataset_dir: Path, tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        "dataset_dir: sample_dataset\noutput_root: output\n", encoding="utf-8"
    )

    assert main(["inspect", "--config", str(config)]) == 0
    assert (tmp_path / "output" / dataset_dir.name / "input" / "introspection.json").exists()


def test_inspect_uses_project_name_for_configured_output(
    dataset_dir: Path, tmp_path: Path
) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        "project_name: sample-project\ndataset_dir: sample_dataset\noutput_root: output\n",
        encoding="utf-8",
    )

    assert main(["inspect", "--config", str(config)]) == 0
    assert (tmp_path / "output" / "sample-project" / "input" / "introspection.json").exists()


def test_inspect_rejects_project_name_outside_output_root(
    dataset_dir: Path, tmp_path: Path
) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        "project_name: ../outside\ndataset_dir: sample_dataset\noutput_root: output\n",
        encoding="utf-8",
    )

    assert main(["inspect", "--config", str(config)]) == 2
    assert not (tmp_path / "outside").exists()


def test_configure_project_writes_the_project_paths(
    dataset_dir: Path,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class Answer:
        def __init__(self, value: str | bool) -> None:
            self.value = value

        def ask(self) -> str | bool:
            return self.value

    class Questionary:
        def __init__(self) -> None:
            self.answers = iter(["sample-project", str(dataset_dir), "./output"])

        def text(self, *_: object, **__: object) -> Answer:
            return Answer(next(self.answers))

        def confirm(self, *_: object, **__: object) -> Answer:
            return Answer(True)

    config = tmp_path / "config.json"
    monkeypatch.setitem(sys.modules, "questionary", Questionary())

    assert main(["configure-project", "--config", str(config)]) == 0
    assert json.loads(config.read_text(encoding="utf-8")) == {
        "project_name": "sample-project",
        "dataset_dir": str(dataset_dir),
        "output_root": "./output",
    }
    assert "Configuration successfully saved to" in capsys.readouterr().out


def test_generate_reads_config_and_cli_overrides_it(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        "project_name: sample-project\ndataset_dir: data\noutput_root: output\n"
        "answers: answers.json\nprofile: core\n",
        encoding="utf-8",
    )
    captured: dict[str, RunConfig] = {}

    def run_pipeline(run_config: RunConfig) -> int:
        captured["config"] = run_config
        return 0

    monkeypatch.setattr(run, "run_pipeline", run_pipeline)

    assert main(["run", "other-data", "--config", str(config), "--profile", "extended"]) == 0
    run_config = captured["config"]
    assert run_config.dataset_dir == Path("other-data")
    assert run_config.profile == "extended"
    assert run_config.output_root == tmp_path / "output"
    assert run_config.answers_path == tmp_path / "answers.json"
    assert run_config.project_name == "sample-project"

    assert main(["generate", "other-data", "--config", str(config), "--profile", "extended"]) == 0


def test_run_reads_llm_command_from_config(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        "dataset_dir: data\noutput_root: output\nprofile: core\n"
        "llm:\n  command: [agent, --safe]\n",
        encoding="utf-8",
    )
    captured: dict[str, RunConfig] = {}

    def capture(value: RunConfig) -> int:
        captured["config"] = value
        return 0

    monkeypatch.setattr(run, "run_pipeline", capture)

    assert main(["run", "--config", str(config)]) == 0
    assert captured["config"].llm_command == ["agent", "--safe"]


def test_module_entry_point_displays_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "xcard_automation", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "approve-proposals" in result.stdout


def test_module_entry_point_reports_parser_errors() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "xcard_automation", "unknown-command"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "invalid choice: 'unknown-command'" in result.stderr


def test_configure_alias_returns_handler_exit_code(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(configure, "_run_config_wizard", lambda _: False)

    assert main(["configure", "--config", str(tmp_path / "config.json")]) == 1


def test_inspect_prints_results_to_stdout(
    dataset_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["inspect", str(dataset_dir)]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["dataset_slug"] == "sample_dataset"
    assert output["file_count"] == 3


def test_run_accepts_all_cli_options(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, RunConfig] = {}

    def run_pipeline(run_config: RunConfig) -> int:
        captured["config"] = run_config
        return 0

    monkeypatch.setattr(run, "run_pipeline", run_pipeline)
    assert (
        main(
            [
                "run",
                "dataset",
                "--profile",
                "core",
                "--output-root",
                "output",
                "--answers",
                "answers.json",
                "--resume",
                "--llm-agent",
                "agent",
                "--mode",
            ]
        )
        == 0
    )
    config = captured["config"]
    assert config.dataset_dir == Path("dataset")
    assert config.profile == "core"
    assert config.output_root == Path("output")
    assert config.answers_path == Path("answers.json")
    assert config.resume is True
    assert config.llm_command == ["agent", "--mode"]


def test_approve_proposals_writes_reviewed_metadata_to_answers(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_dir = tmp_path / "run"
    proposals = run_dir / "automation_output" / "llm_proposals.json"
    proposals.parent.mkdir(parents=True)
    proposals.write_text(
        json.dumps(
            [
                {"path": "identification.name", "value": "Benchmark Dataset"},
                {
                    "path": "authors",
                    "value": [{"given_name": "Ada", "family_name": "Lovelace"}],
                },
                {
                    "path": "citation",
                    "value": {"preferred_citation": {"author": "Ada Lovelace"}},
                },
            ]
        ),
        encoding="utf-8",
    )
    answers = tmp_path / "answers.json"
    answers.write_text("{}", encoding="utf-8")

    assert main(["approve-proposals", str(run_dir), "--answers", str(answers)]) == 0

    assert json.loads(answers.read_text()) == {
        "identification": {"name": "Benchmark Dataset"},
        "authors": [{"given_name": "Ada", "family_name": "Lovelace"}],
        "citation": {"preferred_citation": {"author": "Ada Lovelace"}},
    }
    assert capsys.readouterr().out == "Applied proposals: identification.name, authors, citation\n"


def test_approve_proposals_rejects_malformed_proposals(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_dir = tmp_path / "run"
    proposals = run_dir / "automation_output" / "llm_proposals.json"
    proposals.parent.mkdir(parents=True)
    proposals.write_text(json.dumps(["not a proposal"]), encoding="utf-8")

    assert main(["approve-proposals", str(run_dir), "--answers", str(tmp_path / "answers.json")]) == 2
    assert "xcard-cli: error: Proposals must be objects" in capsys.readouterr().err


@pytest.mark.parametrize(
        ("argv", "message"),
    [
        (["inspect"], "dataset_dir is required"),
        (["run", "dataset"], "profile is required"),
        (["run", "dataset", "--profile", "core"], "output_root is required"),
    ],
)
def test_commands_report_missing_required_configuration(
    argv: list[str], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(argv) == 2
    assert f"xcard-cli: error: {message}" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["evaluate"], "the following arguments are required: DATACARD_FILE"),
    ],
)
def test_argparse_rejects_missing_or_invalid_arguments(
    argv: list[str], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as error:
        main(argv)

    assert error.value.code == 2
    assert message in capsys.readouterr().err


def test_evaluate_reports_text_and_json_results(
    monkeypatch: MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(evaluate, "load_bundle", lambda _: object())
    monkeypatch.setattr(evaluate, "validate_card", lambda *_: [])

    assert main(["evaluate", "card.md"]) == 0
    assert capsys.readouterr().out == "OK\n"

    monkeypatch.setattr(
        evaluate,
        "validate_card",
        lambda *_: [
            {
                "code": "SCHEMA_INVALID",
                "field": "identification.name",
                "severity": "error",
                "message": "required value is missing",
            }
        ],
    )
    assert main(["evaluate", "card.md"]) == 1
    assert capsys.readouterr().out == (
        "FAIL\n"
        "[error] SCHEMA_INVALID identification.name: required value is missing\n"
    )

    assert main(["evaluate", "card.md", "--json"]) == 1
    assert json.loads(capsys.readouterr().out) == ValidationResult(
        [Finding("SCHEMA_INVALID", "identification.name", message="required value is missing")]
    ).as_dict()
