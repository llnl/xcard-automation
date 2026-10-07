from functools import lru_cache
from pathlib import Path
from typing import Any

TOOLS_ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY_ROOT = TOOLS_ROOT / "ontology"
ONTOLOGY_YAML_PATH = ONTOLOGY_ROOT / "genesis.yaml"
ONTOLOGY_TTL_PATH = ONTOLOGY_ROOT / "genesis.ttl"
ONTOLOGY_JSONLD_PATH = ONTOLOGY_ROOT / "genesis.jsonld"
ONTOLOGY_SHACL_PATH = ONTOLOGY_ROOT / "genesis.shacl.ttl"


FIELD_TO_ONTOLOGY_ENUM = {
    "release_status": "release_status_set",
    "workflow.state": "workflow_state_set",
    "access_policy.access_level": "access_level_set",
    "stewardship.level": "stewardship_level_set",
    "object_type": "object_type_set",
    "categorization.science_domain": "OSTI_subject_set",
}


FIELD_ALIASES = {
    "release_status": {
        "draft": "Draft",
        "under_review": "Under_Review",
        "approved": "Approved",
        "published": "Published",
        "deprecated": "Deprecated",
    },
    "workflow.state": {
        "raw": "Raw",
        "processing": "Processing",
        "qa": "QA",
        "analysis": "Analysis",
        "review": "Review",
        "embargo": "Embargo",
        "published": "Published",
        "archived": "Archived",
        "not_applicable": "Not Applicable",
    },
    "access_policy.access_level": {
        "open": "Open",
        "restricted": "Restricted",
        "controlled": "Controlled",
    },
    "stewardship.level": {
        "project_managed": "Project_Managed",
        "repository_managed": "Repository_Managed",
        "externally_managed": "Externally_Managed",
        "not_applicable": "not_applicable",
    },
    "object_type": {
        "dataset": "Dataset",
        "model": "Model",
        "software": "Software",
        "ai_agent": "AI_Agent",
        "eval": "Eval",
        "framework": "Framework",
        "other": "Other",
    },
    "categorization.science_domain": {
        "materials_science": "Materials",
        "biology": "Biology and Medicine",
        "physics": "Physics",
        "chemistry": "Chemistry",
        "climate": "Environmental Sciences",
        "fusion": "Physics",
        "lightsource": "Physics",
        "computer_science": "Mathematics and Computing",
        "other": "Other",
    },
}


@lru_cache(maxsize=1)
def load_ontology_summary() -> dict[str, Any]:
    enums = _parse_enums()
    return {
        "paths": {
            "yaml": str(ONTOLOGY_YAML_PATH),
            "ttl": str(ONTOLOGY_TTL_PATH),
            "jsonld": str(ONTOLOGY_JSONLD_PATH),
            "shacl": str(ONTOLOGY_SHACL_PATH),
        },
        "field_enum_map": FIELD_TO_ONTOLOGY_ENUM,
        "enums": enums,
    }


def allowed_values_for_field(path: str) -> list[str]:
    enum_name = FIELD_TO_ONTOLOGY_ENUM.get(path)
    if not enum_name:
        return []
    return list(load_ontology_summary()["enums"].get(enum_name, []))


def prompt_suffix_for_field(path: str) -> str:
    allowed = allowed_values_for_field(path)
    if not allowed:
        return ""
    rendered = ", ".join(allowed)
    return f" Allowed ontology values: {rendered}."


def alignment_report(metadata: dict[str, Any]) -> dict[str, Any]:
    report: dict[str, Any] = {
        "ontology_yaml": str(ONTOLOGY_YAML_PATH),
        "checked_fields": {},
    }
    for path, enum_name in FIELD_TO_ONTOLOGY_ENUM.items():
        value = _get_path(metadata, path)
        if value in (None, "", [], {}):
            continue
        allowed = set(load_ontology_summary()["enums"].get(enum_name, []))
        canonical = canonicalize_value(path, value)
        report["checked_fields"][path] = {
            "value": value,
            "canonical_ontology_value": canonical,
            "ontology_enum": enum_name,
            "matches_ontology": canonical in allowed,
            "allowed_values": sorted(allowed),
        }
    return report


def canonicalize_value(path: str, value: Any) -> Any:
    if not isinstance(value, str):
        return value
    alias_map = FIELD_ALIASES.get(path, {})
    return alias_map.get(value, alias_map.get(value.lower(), value))


def _parse_enums() -> dict[str, list[str]]:
    if not ONTOLOGY_YAML_PATH.exists():
        return {}
    lines = ONTOLOGY_YAML_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    enums: dict[str, list[str]] = {}
    in_enums = False
    current_enum: str | None = None
    in_values = False
    for line in lines:
        if line.startswith("enums:"):
            in_enums = True
            continue
        if not in_enums:
            continue
        if line.startswith("version:"):
            break
        if line.startswith("  ") and not line.startswith("    ") and line.rstrip().endswith(":"):
            current_enum = line.strip().rstrip(":")
            enums[current_enum] = []
            in_values = False
            continue
        if current_enum and line.strip() == "permissible_values:":
            in_values = True
            continue
        if current_enum and in_values:
            if line.startswith("      ") and line.rstrip().endswith(": {}"):
                value = line.strip()[:-3].rstrip(":").strip("'\"")
                enums[current_enum].append(value)
                continue
            if line.startswith("    ") and not line.startswith("      "):
                in_values = False
    return enums


def _get_path(data: Any, path: str) -> Any:
    current = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
        if current is None:
            return None
    return current
