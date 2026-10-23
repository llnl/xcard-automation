import argparse
from pathlib import Path
from typing import Literal

from xcard_automation.core.utils import write_json_file

from ..config import ConfigError, validate_project_name


def add_command(
    subparsers: argparse._SubParsersAction,
    formatter_class: type[argparse.HelpFormatter] = argparse.HelpFormatter
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "configure-project",
        aliases=["configure"],
        help="Interactively configure project settings",
        formatter_class=formatter_class
    )

    # Optional Argument
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.json"),
        metavar="CONFIG_FILE",
        help="Path to the configuration file to save (default: config.json)"
    )

    return parser


def _run_config_wizard(config_path: Path):
    """Internal helper to handle the interactive prompts."""
    try:
        import questionary
    except ImportError:
        print("❌ Error: 'questionary' library not found.")
        print("Please install it using: pip install questionary")
        return False

    print("\n🚀 Project Configuration Wizard")
    print(f"Settings will be saved to: {config_path.absolute()}\n")

    def validate_name(text: str) -> str | Literal[True]:
        try:
            validate_project_name(text)
        except ConfigError as error:
            return str(error)
        else:
            return True

    def validate_dataset_dir(text: str) -> str | Literal[True]:
        if not text:
            return "Directory path cannot be empty."
        if not Path(text).is_dir():
            return f"The path '{text}' does not exist or is not a directory."
        return True

    config_data = {}
    config_data["project_name"] = questionary.text(
        "Project name (no spaces):",
        validate=validate_name,
    ).ask()

    config_data["dataset_dir"] = questionary.text(
        "Dataset root folder:",
        validate=validate_dataset_dir,
    ).ask()

    config_data["output_root"] = questionary.text(
        "Output root folder:",
        default="./output",
        validate=lambda text: (
            True if text else "Directory path cannot be empty."
        ),
    ).ask()

    print("\n--- Configuration Summary ---")
    for key, value in config_data.items():
        label = key.replace('_', ' ').title()
        print(f"{label}: {value}")

    confirm = questionary.confirm("\nDoes this look correct?").ask()

    if confirm:
        try:
            # Use your project's utility for consistency
            write_json_file(config_path, config_data)
            print(f"\n✅ Configuration successfully saved to {config_path.absolute()}")
        except OSError as e:
            print(f"\n❌ Error saving config file: {e}")
            return False
        else:
            return True
    else:
        print("\n⚠️ Configuration cancelled. No changes were saved.")
        return False


def handle(args: argparse.Namespace) -> int:
    success = _run_config_wizard(args.config)
    return 0 if success else 1
