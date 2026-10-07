from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..core.contract import DEFAULT_TEMPLATE_PATH
from ..core.introspect import inspect_dataset
from ..core.pipeline import RunConfig, run_pipeline
from ..core.validator import validate_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Datacard automation pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a dataset directory")
    inspect_parser.add_argument("dataset_dir", type=Path)
    inspect_parser.add_argument("--output", type=Path)

    run_parser = subparsers.add_parser("run", help="Run the datacard pipeline")
    run_parser.add_argument("dataset_dir", type=Path)
    run_parser.add_argument("--profile", required=True, choices=["core", "extended", "ai_ready", "sensitive"])
    run_parser.add_argument("--output-root", type=Path)
    run_parser.add_argument("--answers", type=Path)
    run_parser.add_argument("--resume", action="store_true")
    run_parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE_PATH)

    validate_parser = subparsers.add_parser("validate", help="Validate a rendered datacard")
    validate_parser.add_argument("datacard", type=Path)
    validate_parser.add_argument("--json", dest="emit_json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "inspect":
        payload = inspect_dataset(args.dataset_dir)
        if args.output:
            args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        else:
            print(json.dumps(payload, indent=2))
        return 0

    if args.command == "run":
        config = RunConfig(
            dataset_dir=args.dataset_dir,
            profile=args.profile,
            output_root=args.output_root,
            answers_path=args.answers,
            resume=args.resume,
            template_path=args.template,
        )
        return run_pipeline(config)

    if args.command == "validate":
        result = validate_file(args.datacard)
        if args.emit_json:
            print(json.dumps(result.as_dict(), indent=2))
        else:
            print("OK" if result.ok else "FAIL")
            for finding in result.findings:
                print(f"[{finding.severity}] {finding.code} {finding.field}: {finding.message}")
        return 0 if result.ok else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
