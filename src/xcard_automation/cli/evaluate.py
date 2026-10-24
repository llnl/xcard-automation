import argparse
import json
from pathlib import Path

from xcard_automation.core.evaluation import validate_card
from xcard_automation.core.schema_bundle import load_bundle
from xcard_automation.core.validator import Finding, ValidationResult


def add_command(
    subparsers: argparse._SubParsersAction,
    formatter_class: type[argparse.HelpFormatter] = argparse.HelpFormatter,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "evaluate",
        help="Evaluate a rendered datacard",
        formatter_class=formatter_class,
    )

    # Positional Arguments
    parser.add_argument(
        "datacard",
        type=Path,
        metavar="DATACARD_FILE",
        help="Path to the rendered datacard file to validate",
    )
    parser.add_argument(
        "--schema-bundle",
        type=Path,
        metavar="BUNDLE_DIR",
        help="Local schema bundle directory (default: packaged Genesis 1.2 bundle)",
    )

    # Output Options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--json",
        dest="emit_json",
        action="store_true",
        help="Emit validation results as JSON for machine consumption",
    )


def handle(args: argparse.Namespace) -> int:
    bundle = load_bundle(args.schema_bundle)
    result = ValidationResult(
        [
            Finding(
                finding["code"] or "SCHEMA_INVALID",
                finding["field"] or "(document)",
                finding["severity"] or "error",
                finding["message"] or "",
            )
            for finding in validate_card(args.datacard, bundle)
        ]
    )
    if args.emit_json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print("OK" if result.ok else "FAIL")
        for finding in result.findings:
            print(f"[{finding.severity}] {finding.code} {finding.field}: {finding.message}")
    return 0 if result.ok else 1
