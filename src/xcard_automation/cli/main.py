import argparse
import sys

from .commands.registry import COMMANDS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="""
Datacard Automation Pipeline
============================
A tool for inspecting datasets, generating standardized datacards, 
and validating them against organizational compliance rules.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Use 'datacard <command> --help' for more information on a specific command."
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Available commands"
    )

    # Register all commands from the COMMANDS map
    for cmd_module in COMMANDS.values():
        cmd_module.add_command(
            subparsers,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Dispatch to the appropriate handler
    handler_module = COMMANDS.get(args.command)
    if handler_module:
        return handler_module.handle(args)

    return 1


if __name__ == "__main__":
    sys.exit(main())
