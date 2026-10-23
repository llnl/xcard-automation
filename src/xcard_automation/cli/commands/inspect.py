import argparse
import json
from pathlib import Path

from xcard_automation.core.artifacts import prepare_run_dirs
from xcard_automation.core.introspect import inspect_dataset
from xcard_automation.core.utils import write_json_file

from ..config import ConfigError, apply_config


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
        nargs="?",
        metavar="DATASET_DIR",
        help="Path to the directory containing the dataset to inspect"
    )

    # Output Options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--output-root",
        type=Path,
        metavar="OUTPUT_DIR",
        help="Write the inspection results to a inspect_results.jsonfile instead of stdout"
    )
    parser.add_argument(
        "--config",
        type=Path,
        metavar="CONFIG_FILE",
        help="Path to a project configuration file"
    )

    return parser


def handle(args: argparse.Namespace) -> int:
    apply_config(
        args,
        {"dataset_dir": ("dataset_dir",), "output_root": ("output_root",)},
        value_fields=("project_name",),
    )
    if args.dataset_dir is None:
        raise ConfigError("dataset_dir is required (pass it or set it in --config)")
    introspection = inspect_dataset(args.dataset_dir)
    dataset_slug = introspection["dataset_slug"]

    if args.output_root:
        run_dirs = prepare_run_dirs(
            args.output_root, getattr(args, "project_name", None) or dataset_slug
        )

        output_path = run_dirs["input"] / "introspection.json"
        write_json_file(output_path, introspection)

        print(f"Results written to: {output_path}")
    else:
        print(json.dumps(introspection, indent=2))
    return 0
