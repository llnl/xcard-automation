import argparse
import json
from pathlib import Path

from ...core.introspect import inspect_dataset


def add_command(subparsers: argparse._SubParsersAction):
    parser = subparsers.add_parser("inspect", help="Inspect a dataset directory")
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def handle(args: argparse.Namespace) -> int:
    payload = inspect_dataset(args.dataset_dir)
    if args.output:
        args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    else:
        print(json.dumps(payload, indent=2))
    return 0
