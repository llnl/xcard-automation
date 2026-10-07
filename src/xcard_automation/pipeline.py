from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
from shutil import copy2
from typing import Any

from .artifacts import prepare_run_dirs, write_run_inputs
from .contract import DEFAULT_TEMPLATE_PATH
from .introspect import build_checksum_manifest, inspect_dataset
from .mapper import build_metadata
from .ontology import alignment_report, load_ontology_summary
from .questionnaire import collect_answers
from .renderer import render_datacard
from .utils import load_yaml_file, write_json_file
from .validator import (
    render_validation_summary,
    validate_file,
    validate_metadata,
)


@dataclass
class RunConfig:
    dataset_dir: Path
    profile: str
    output_root: Path | None = None
    answers_path: Path | None = None
    resume: bool = False
    template_path: Path = DEFAULT_TEMPLATE_PATH


def run_pipeline(config: RunConfig) -> int:
    dataset_dir = config.dataset_dir.resolve()
    introspection = inspect_dataset(dataset_dir)
    dataset_slug = introspection["dataset_slug"]
    run_dirs = prepare_run_dirs(config.output_root, dataset_slug)
    answers_path = config.answers_path or (run_dirs["input"] / "answers.yaml")
    answers = load_yaml_file(answers_path, {})
    checksum_info = build_checksum_manifest(dataset_dir, run_dirs["automation_output"] / "checksums.sha256")
    resume_created_date = answers.get("datacard.created_date") if isinstance(answers, dict) and config.resume else None
    metadata = build_metadata(dataset_dir, config.profile, introspection, answers, checksum_info, resume_created_date)
    unresolved = _missing_required_fields(config.profile, metadata)
    if unresolved:
        answers = collect_answers(metadata, answers, unresolved)
        metadata = build_metadata(dataset_dir, config.profile, introspection, answers, checksum_info, resume_created_date)
        unresolved = _missing_required_fields(config.profile, metadata)

    source_manifest = {
        "dataset_dir": str(dataset_dir),
        "profile": config.profile,
        "template_path": str(config.template_path),
        "output_root": str(run_dirs["root"]),
        "resume": config.resume,
        "ontology_yaml": load_ontology_summary()["paths"]["yaml"],
        "ontology_shacl": load_ontology_summary()["paths"]["shacl"],
    }
    write_run_inputs(run_dirs, source_manifest, introspection, answers)
    write_json_file(run_dirs["input"] / "ontology_summary.json", load_ontology_summary())

    if unresolved:
        write_json_file(run_dirs["automation_output"] / "unresolved_fields.json", {"missing_fields": unresolved})
        return 1

    write_json_file(run_dirs["automation_output"] / "normalized_metadata.json", metadata)
    write_json_file(run_dirs["automation_output"] / "ontology_alignment.json", alignment_report(metadata))
    datacard_path = run_dirs["automation_output"] / metadata["datacard"]["filename"]
    datacard_path.write_text(render_datacard(metadata), encoding="utf-8")

    result = validate_file(datacard_path)
    write_json_file(run_dirs["validation_output"] / "validation_report.json", result.as_dict())
    (run_dirs["validation_output"] / "validation_summary.md").write_text(
        render_validation_summary(result),
        encoding="utf-8",
    )
    if result.ok:
        copy2(datacard_path, run_dirs["validation_output"] / datacard_path.name)
        return 0
    return 1


def _missing_required_fields(profile: str, metadata: dict[str, Any]) -> list[str]:
    validation = validate_metadata(metadata)
    missing = []
    for finding in validation.findings:
        if finding.code == "MISSING_REQUIRED":
            missing.append(finding.field)
    return sorted(set(missing))
