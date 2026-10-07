from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from .contract import DEFAULT_OUTPUT_ROOT
from .utils import ensure_dir, write_json_file, write_yaml_file


def prepare_run_dirs(output_root: Path | None, dataset_slug: str) -> dict[str, Path]:
    root = ensure_dir((output_root or DEFAULT_OUTPUT_ROOT) / dataset_slug)
    input_dir = ensure_dir(root / "input")
    automation_dir = ensure_dir(root / "automation_output")
    validation_dir = ensure_dir(root / "validation_output")
    return {
        "root": root,
        "input": input_dir,
        "automation_output": automation_dir,
        "validation_output": validation_dir,
    }


def write_run_inputs(run_dirs: dict[str, Path], source_manifest: dict, introspection: dict, answers: dict) -> None:
    write_json_file(run_dirs["input"] / "source_manifest.json", source_manifest)
    write_json_file(run_dirs["input"] / "introspection.json", introspection)
    write_yaml_file(run_dirs["input"] / "answers.yaml", answers)
