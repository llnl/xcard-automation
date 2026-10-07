from __future__ import annotations

import argparse
import sys

from .commands.registry import COMMANDS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Datacard automation pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Register all commands from the COMMANDS map
    for cmd_module in COMMANDS.values():
        cmd_module.add_command(subparsers)
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
