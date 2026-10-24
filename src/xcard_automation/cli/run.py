import argparse
from pathlib import Path

from xcard_automation.core.pipeline import RunConfig, run_pipeline

from .config import ConfigError, apply_config
from xcard_automation.core.utils import load_yaml_file


def add_command(
    subparsers: argparse._SubParsersAction,
    formatter_class: type[argparse.HelpFormatter] = argparse.HelpFormatter,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "run",
        aliases=["generate"],
        help="Run the full datacard generation pipeline",
        formatter_class=formatter_class,
    )

    # 1. Positional Arguments
    parser.add_argument(
        "dataset_dir",
        type=Path,
        nargs="?",
        metavar="DATASET_DIR",  # Hint: Tells user what this is
        help="Path to the directory containing the dataset to process",
    )

    # 2. Use Argument Groups to organize the --help output
    config_group = parser.add_argument_group("Pipeline Configuration")

    config_group.add_argument(
        "--profile",
        help="Profile supported by the selected schema bundle",
    )
    config_group.add_argument(
        "--schema-bundle",
        type=Path,
        metavar="BUNDLE_DIR",
        help="Local schema bundle directory (default: packaged Genesis 1.2 bundle)",
    )
    config_group.add_argument(
        "--llm-agent",
        nargs=argparse.REMAINDER,
        metavar="COMMAND",
        help="External agent command that reads a crawl request from stdin and writes evidence JSON to stdout",
    )
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--output-root",
        type=Path,
        metavar="OUTPUT_DIR",
        help="Root directory where generated cards will be saved",
    )
    output_group.add_argument(
        "--answers",
        type=Path,
        metavar="ANSWERS_JSON",
        help="Path to a JSON file containing pre-filled answers",
    )
    output_group.add_argument(
        "--resume",
        action="store_true",
        help="Resume from the last successful checkpoint if available",
    )
    parser.add_argument(
        "--config",
        type=Path,
        metavar="CONFIG_FILE",
        help="Path to a project configuration file",
    )

    return parser


def handle(args: argparse.Namespace) -> int:
    apply_config(
        args,
        {
            "dataset_dir": ("dataset_dir",),
            "output_root": ("output_root",),
            "answers": ("answers", "answers_file"),
            "schema_bundle": ("schema_bundle",),
        },
        value_fields=("profile", "project_name"),
    )
    if args.dataset_dir is None:
        raise ConfigError("dataset_dir is required (pass it or set it in --config)")
    if args.profile is None:
        raise ConfigError("profile is required (pass it or set it in --config)")
    if args.output_root is None:
        raise ConfigError("output_root is required (pass it or set it in --config)")
    if args.llm_agent is None and args.config:
        config_data = load_yaml_file(args.config, {})
        llm = config_data.get("llm", {}) if isinstance(config_data, dict) else {}
        command = llm.get("command") if isinstance(llm, dict) else None
        if command is not None:
            if not isinstance(command, list) or not all(isinstance(part, str) for part in command):
                raise ConfigError("llm.command must be a list of command arguments")
            args.llm_agent = command
    config = RunConfig(
        dataset_dir=args.dataset_dir,
        profile=args.profile,
        output_root=args.output_root,
        answers_path=args.answers,
        resume=args.resume,
        schema_bundle=args.schema_bundle or RunConfig.schema_bundle,
        project_name=getattr(args, "project_name", None),
        llm_command=args.llm_agent,
    )
    return run_pipeline(config)
