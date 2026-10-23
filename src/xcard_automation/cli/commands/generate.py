import argparse
from pathlib import Path

from xcard_automation.core.contract import DEFAULT_TEMPLATE_PATH
from xcard_automation.core.pipeline import RunConfig, run_pipeline

from ..config import ConfigError, apply_config


def add_command(
    subparsers: argparse._SubParsersAction,
    formatter_class: type[argparse.HelpFormatter] = argparse.HelpFormatter
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "generate",
        aliases=["run"],
        help="Run the full datacard generation pipeline",
        formatter_class=formatter_class
    )

    # 1. Positional Arguments
    parser.add_argument(
        "dataset_dir",
        type=Path,
        nargs="?",
        metavar="DATASET_DIR",  # Hint: Tells user what this is
        help="Path to the directory containing the dataset to process"
    )

    # 2. Use Argument Groups to organize the --help output
    config_group = parser.add_argument_group("Pipeline Configuration")

    config_group.add_argument(
        "--profile",
        choices=["core", "extended", "ai_ready", "sensitive"],
        help="The compliance profile to use for generation"
    )
    config_group.add_argument(
        "--template",
        type=Path,
        default=DEFAULT_TEMPLATE_PATH,
        metavar="TEMPLATE_FILE",
        help=f"Path to the Jinja2 template (default: {DEFAULT_TEMPLATE_PATH})"
    )

    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--output-root",
        type=Path,
        metavar="OUTPUT_DIR",
        help="Root directory where generated cards will be saved"
    )
    output_group.add_argument(
        "--answers",
        type=Path,
        metavar="ANSWERS_JSON",
        help="Path to a JSON file containing pre-filled answers"
    )
    output_group.add_argument(
        "--resume",
        action="store_true",
        help="Resume from the last successful checkpoint if available"
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
        {
            "dataset_dir": ("dataset_dir",),
            "output_root": ("output_root",),
            "answers": ("answers", "answers_file"),
        },
        value_fields=("profile",),
    )
    if args.dataset_dir is None:
        raise ConfigError("dataset_dir is required (pass it or set it in --config)")
    if args.profile is None:
        raise ConfigError("profile is required (pass it or set it in --config)")
    if args.profile not in {"core", "extended", "ai_ready", "sensitive"}:
        raise ConfigError(f"Invalid profile: {args.profile}")
    config = RunConfig(
        dataset_dir=args.dataset_dir,
        profile=args.profile,
        output_root=args.output_root,
        answers_path=args.answers,
        resume=args.resume,
        template_path=args.template,
    )
    return run_pipeline(config)
