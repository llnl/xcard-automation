import sys
from typing import Any

from .contract import PROMPT_BATCHES
from .ontology import prompt_suffix_for_field
from .utils import get_path, parse_user_value


def collect_answers(metadata: dict[str, Any], answers: dict[str, Any], missing_fields: list[str]) -> dict[str, Any]:
    if not sys.stdin.isatty():
        return answers

    unresolved = set(missing_fields)
    updated = dict(answers)
    for batch in PROMPT_BATCHES:
        batch_fields = [field for field in batch if field.path in unresolved]
        if not batch_fields:
            continue
        print()
        for field in batch_fields:
            existing = answers.get(field.path, get_path(metadata, field.path, ""))
            prompt = f"{field.prompt}{prompt_suffix_for_field(field.path)}"
            if existing not in ("", None):
                prompt += f" [{existing}]"
            prompt += ": "
            raw = input(prompt)
            if not raw.strip():
                continue
            updated[field.path] = parse_user_value(raw)
    return updated
