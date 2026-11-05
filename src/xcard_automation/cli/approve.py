"""Apply reviewed LLM metadata proposals to an answers file."""

import argparse
from pathlib import Path
from typing import Any

from xcard_automation.core.utils import get_path, is_missing, load_yaml_file, set_path, write_yaml_file

from .config import ConfigError


APPROVABLE_PATHS = {"identification.name", "authors", "citation"}


def add_command(
    subparsers: argparse._SubParsersAction,
    formatter_class: type[argparse.HelpFormatter] = argparse.HelpFormatter,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "approve-proposals",
        help="Apply reviewed LLM metadata proposals to an answers file",
        formatter_class=formatter_class,
    )
    parser.add_argument("run_dir", type=Path, metavar="RUN_DIR")
    parser.add_argument("--answers", type=Path, required=True, metavar="ANSWERS_FILE")
    parser.add_argument(
        "--field",
        action="append",
        choices=sorted(APPROVABLE_PATHS),
        help="Apply only this proposal field (repeatable)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing answer for an approved field",
    )
    return parser


def handle(args: argparse.Namespace) -> int:
    proposal_path = args.run_dir / "automation_output" / "llm_proposals.json"
    proposals = load_yaml_file(proposal_path, None)
    if not isinstance(proposals, list):
        raise ConfigError(f"Proposal file not found or invalid: {proposal_path}")
    if not all(isinstance(proposal, dict) for proposal in proposals):
        raise ConfigError("Proposals must be objects")
    requested = set(args.field or APPROVABLE_PATHS)
    selected = [proposal for proposal in proposals if proposal.get("path") in requested]
    if not selected:
        raise ConfigError("No matching proposals to approve")
    paths = [proposal.get("path") for proposal in selected]
    if len(paths) != len(set(paths)):
        raise ConfigError("Proposals must have one unique path each")

    answers = load_yaml_file(args.answers, {})
    if not isinstance(answers, dict):
        raise ConfigError("Answers file must contain a mapping")
    applied: list[str] = []
    for proposal in selected:
        path = proposal["path"]
        value = proposal.get("value")
        _validate_proposal(path, value)
        if not args.force and not is_missing(get_path(answers, path)):
            raise ConfigError(f"Answer already exists for {path}; pass --force to replace it")
        set_path(answers, path, value)
        applied.append(path)
    write_yaml_file(args.answers, answers)
    print(f"Applied proposals: {', '.join(applied)}")
    return 0


def _validate_proposal(path: str, value: Any) -> None:
    if path not in APPROVABLE_PATHS:
        raise ConfigError(f"Proposal path is not approvable: {path}")
    if path == "identification.name" and (not isinstance(value, str) or not value.strip()):
        raise ConfigError("identification.name must be a non-empty string")
    if path == "authors" and (
        not isinstance(value, list)
        or not value
        or not all(
            isinstance(author, dict)
            and isinstance(author.get("given_name"), str)
            and isinstance(author.get("family_name"), str)
            and author["given_name"].strip()
            and author["family_name"].strip()
            for author in value
        )
    ):
        raise ConfigError("authors must be a non-empty list of named people")
    if path == "citation" and not isinstance(value, dict):
        raise ConfigError("citation must be an object")
