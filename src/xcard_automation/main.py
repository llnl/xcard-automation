import argparse
import sys

from .cli.registry import COMMANDS
from .cli.config import ConfigError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="""
Datacard Automation Pipeline
============================
A tool for inspecting datasets, generating standardized datacards,
and validating them against organizational compliance rules.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Use 'datacard <command> --help' for more information on a specific command.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Available commands",
    )

    for cmd_module in dict.fromkeys(COMMANDS.values()):
        cmd_module.add_command(
            subparsers,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handler_module = COMMANDS.get(args.command)
    if handler_module:
        try:
            return handler_module.handle(args)
        except ConfigError as error:
            print(f"xcard-cli: error: {error}", file=sys.stderr)
            return 2
    return 1
