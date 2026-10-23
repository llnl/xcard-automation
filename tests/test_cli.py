import json
import sys
from pathlib import Path

from pytest import MonkeyPatch

from xcard_automation.cli.main import main
from xcard_automation.cli.commands import generate
from xcard_automation.core.pipeline import RunConfig


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
    dataset_dir: Path, monkeypatch: MonkeyPatch, tmp_path: Path
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

    monkeypatch.setattr(generate, "run_pipeline", run_pipeline)

    assert main(["generate", "other-data", "--config", str(config), "--profile", "extended"]) == 0
    run_config = captured["config"]
    assert run_config.dataset_dir == Path("other-data")
    assert run_config.profile == "extended"
    assert run_config.output_root == tmp_path / "output"
    assert run_config.answers_path == tmp_path / "answers.json"
    assert run_config.project_name == "sample-project"
