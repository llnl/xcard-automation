import json
import re
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any

import yaml

PLACEHOLDER_RE = re.compile(r"\$\{[^}]+\}|__[^_\n][^_\n]*__|\[!TODO\]|<REPLACE:|<INSTRUCTIONS:|<metadata_key:")


def snake_case(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def today_iso() -> str:
    return date.today().isoformat()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_yaml_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return deepcopy(default)
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return deepcopy(default)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = yaml.safe_load(text)
    return deepcopy(default) if data is None else data


def dump_yaml(data: Any) -> str:
    return json.dumps(data, indent=2)


def write_yaml_file(path: Path, data: Any) -> None:
    path.write_text(dump_yaml(data), encoding="utf-8")


def write_json_file(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=False), encoding="utf-8")


def get_path(data: Any, path: str, default: Any = None) -> Any:
    current = data
    for part in _split_path(path):
        if isinstance(part, int):
            if not isinstance(current, list) or part >= len(current):
                return default
            current = current[part]
        else:
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
    return current


def set_path(data: dict[str, Any], path: str, value: Any) -> None:
    current: Any = data
    parts = _split_path(path)
    for index, part in enumerate(parts[:-1]):
        next_part = parts[index + 1]
        if isinstance(part, int):
            while len(current) <= part:
                current.append({} if not isinstance(next_part, int) else [])
            current = current[part]
            continue
        if part not in current or current[part] is None:
            current[part] = [] if isinstance(next_part, int) else {}
        current = current[part]
    last = parts[-1]
    if isinstance(last, int):
        while len(current) <= last:
            current.append(None)
        current[last] = value
    else:
        current[last] = value


def flatten_answers(data: dict[str, Any]) -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, value in data.items():
        if "." in key or "[" in key:
            flattened[key] = value
        elif isinstance(value, dict):
            for child_key, child_value in flatten_answers(value).items():
                flattened[f"{key}.{child_key}"] = child_value
        else:
            flattened[key] = value
    return flattened


def deep_merge(base: Any, update: Any) -> Any:
    if isinstance(base, dict) and isinstance(update, dict):
        merged = {key: deepcopy(value) for key, value in base.items()}
        for key, value in update.items():
            merged[key] = deep_merge(merged.get(key), value) if key in merged else deepcopy(value)
        return merged
    return deepcopy(update)


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip() or value.strip() in {"null", "None"}
    if isinstance(value, list):
        return len(value) == 0
    if isinstance(value, dict):
        return len(value) == 0
    return False


def parse_user_value(raw: str) -> Any:
    text = raw.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def sanitize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def read_text_if_exists(path: str | Path) -> str:
    candidate = Path(path)
    if not candidate.exists():
        return ""
    return candidate.read_text(encoding="utf-8", errors="replace")


def has_placeholders(text: str) -> bool:
    return bool(PLACEHOLDER_RE.search(text))


def _split_path(path: str) -> list[str | int]:
    parts: list[str | int] = []
    for token in path.split("."):
        if "[" not in token:
            parts.append(token)
            continue
        name, rest = token.split("[", 1)
        if name:
            parts.append(name)
        indices = re.findall(r"\[(\d+)\]", "[" + rest)
        parts.extend(int(idx) for idx in indices)
    return parts
