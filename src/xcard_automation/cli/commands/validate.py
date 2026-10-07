import argparse
import json
from pathlib import Path

from ...core.validator import validate_file


def add_command(subparsers: argparse._SubParsersAction):
    parser = subparsers.add_parser("validate", help="Validate a rendered datacard")
    parser.add_argument("datacard", type=Path)
    parser.add_argument("--json", dest="emit_json", action="store_true")
    return parser


def handle(args: argparse.Namespace) -> int:
    result = validate_file(args.datacard)
    if args.emit_json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print("OK" if result.ok else "FAIL")
        for finding in result.findings:
            print(f"[{finding.severity}] {finding.code} {finding.field}: {finding.message}")
    return 0 if result.ok else 1
