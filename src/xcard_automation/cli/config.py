"""Shared project-config loading for commands that consume dataset paths."""

from argparse import Namespace
from pathlib import Path
from typing import Any

from xcard_automation.core.utils import load_yaml_file


class ConfigError(ValueError):
    """A project configuration could not be used."""


def validate_project_name(value: object) -> str:
    """Ensure a project name remains within the configured output root."""
    if not isinstance(value, str) or not value:
        raise ConfigError("project_name must be a non-empty string")
    if any(char.isspace() for char in value):
        raise ConfigError("project_name cannot contain spaces")
    if value in {".", ".."} or "/" in value or "\\" in value:
        raise ConfigError("project_name must be a single directory name")
    return value


def apply_config(
    args: Namespace,
    path_fields: dict[str, tuple[str, ...]],
    value_fields: tuple[str, ...] = (),
) -> Namespace:
    """Fill unset command arguments from ``--config``.

    Values supplied on the command line take precedence. Paths read from the
    config are relative to that file, so a project config is portable.
    """
    if args.config is None:
        return args

    config_path = args.config
    if not config_path.is_file():
        raise ConfigError(f"Configuration file not found: {config_path}")
    config = load_yaml_file(config_path, {})
    if not isinstance(config, dict):
        raise ConfigError("Configuration file must contain a mapping")

    for field, keys in path_fields.items():
        if getattr(args, field) is not None:
            continue
        value = _first_value(config, keys)
        if value is None:
            continue
        if not isinstance(value, str):
            raise ConfigError(f"Configuration value '{keys[0]}' must be a string")
        setattr(args, field, _config_path(config_path, value))

    for field in value_fields:
        if getattr(args, field, None) is None and field in config:
            value = config[field]
            if field == "project_name":
                value = validate_project_name(value)
            setattr(args, field, value)
    return args


def _first_value(config: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in config:
            return config[key]
    return None


def _config_path(config_path: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else config_path.parent / path
