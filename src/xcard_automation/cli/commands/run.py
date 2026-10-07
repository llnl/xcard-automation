import argparse
from pathlib import Path

from ...core.contract import DEFAULT_TEMPLATE_PATH
from ...core.pipeline import RunConfig, run_pipeline


def add_command(subparsers: argparse._SubParsersAction):
    parser = subparsers.add_parser("run", help="Run the datacard pipeline")
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("--profile", required=True, choices=["core", "extended", "ai_ready", "sensitive"])
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--answers", type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE_PATH)
    return parser


def handle(args: argparse.Namespace) -> int:
    config = RunConfig(
        dataset_dir=args.dataset_dir,
        profile=args.profile,
        output_root=args.output_root,
        answers_path=args.answers,
        resume=args.resume,
        template_path=args.template,
    )
    return run_pipeline(config)
