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


def test_generate_reads_config_and_cli_overrides_it(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        "dataset_dir: data\noutput_root: output\nanswers: answers.json\nprofile: core\n",
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
