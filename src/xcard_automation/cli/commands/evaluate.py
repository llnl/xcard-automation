import argparse
import json
from pathlib import Path

from xcard_automation.core.validator import validate_file


def add_command(
    subparsers: argparse._SubParsersAction,
    formatter_class: type[argparse.HelpFormatter] = argparse.HelpFormatter
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "evaluate",
        help="Evaluate a rendered datacard",
        formatter_class=formatter_class
    )

    # Positional Arguments
    parser.add_argument(
        "datacard",
        type=Path,
        metavar="DATACARD_FILE",
        help="Path to the rendered datacard file to validate"
    )

    # Output Options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--json",
        dest="emit_json",
        action="store_true",
        help="Emit validation results as JSON for machine consumption"
    )


def handle(args: argparse.Namespace) -> int:
    result = validate_file(args.datacard)
    if args.emit_json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print("OK" if result.ok else "FAIL")
        for finding in result.findings:
            print(f"[{finding.severity}] {finding.code} {finding.field}: {finding.message}")
    return 0 if result.ok else 1
