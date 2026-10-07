import argparse
import json
from pathlib import Path

from ...core.introspect import inspect_dataset


def add_command(
    subparsers: argparse._SubParsersAction,
    formatter_class: type[argparse.HelpFormatter] = argparse.HelpFormatter
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "inspect",
        help="Inspect a dataset directory",
        formatter_class=formatter_class
    )

    # Positional Arguments
    parser.add_argument(
        "dataset_dir",
        type=Path,
        metavar="DATASET_DIR",
        help="Path to the directory containing the dataset to inspect"
    )

    # Output Options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--output",
        type=Path,
        metavar="OUTPUT_FILE",
        help="Write the inspection results to a JSON file instead of stdout"
    )

    return parser


def handle(args: argparse.Namespace) -> int:
    payload = inspect_dataset(args.dataset_dir)
    if args.output:
        args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    else:
        print(json.dumps(payload, indent=2))
    return 0
