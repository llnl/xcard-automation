"""Load, project, render, and validate local schema bundles."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
import sys
from typing import Any
from urllib.parse import urlparse

import yaml
from jinja2 import Environment, StrictUndefined
import questionary

from .utils import get_path, is_missing, parse_user_value, set_path


@dataclass(frozen=True)
class SchemaBundle:
    root: Path
    manifest: dict[str, Any]
    mapping: dict[str, Any]
    schema: dict[str, Any]

    @property
    def id(self) -> str:
        return self.manifest["id"]

    @property
    def version(self) -> str:
        return self.manifest["version"]

    @property
    def template_path(self) -> Path:
        return self.root / self.manifest["template"]

    @property
    def schema_path(self) -> Path:
        return (self.root / self.manifest["linkml_schema"]).resolve()

    @property
    def ontology_path(self) -> Path | None:
        ontology = self.manifest.get("ontology")
        return self.root / ontology if ontology else None

    @property
    def automation_policy_path(self) -> Path | None:
        policy = self.manifest.get("automation_policy")
        return self.root / policy if policy else None

    @property
    def output_filename(self) -> str:
        return self.manifest.get("output_filename", "datacard.md")


def default_bundle_path() -> Path:
    return Path(__file__).resolve().parents[1] / "schemas" / "genesis-1.2"


def load_bundle(path: Path | None = None) -> SchemaBundle:
    root = (path or default_bundle_path()).resolve()
    manifest = _load_yaml(root / "bundle.yaml")
    for key in ("id", "version", "template", "linkml_schema", "root_class", "mapping"):
        if key not in manifest:
            raise ValueError(f"{root / 'bundle.yaml'} is missing {key}")
    template_path = root / manifest["template"]
    if template_path.suffix != ".j2" or not template_path.is_file():
        raise ValueError(f"Bundle template must be an existing .j2 file: {template_path}")
    schema = _load_yaml((root / manifest["linkml_schema"]).resolve())
    if manifest.get("root_class") not in schema.get("classes", {}):
        raise ValueError("Bundle root_class must name a class in the LinkML schema")
    mapping = _load_yaml(root / manifest["mapping"])
    if not isinstance(mapping.get("fields"), list):
        raise ValueError("Bundle mapping must contain a fields list")
    if "profiles" in manifest and not isinstance(manifest["profiles"], list):
        raise ValueError("Bundle profiles must be a list when declared")
    if "ontology" in manifest:
        ontology_path = root / manifest["ontology"]
        if ontology_path.suffix not in {".yaml", ".yml"} or not ontology_path.is_file():
            raise ValueError(f"Bundle ontology must be an existing YAML file: {ontology_path}")
    return SchemaBundle(root, manifest, mapping, schema)


def project_model(bundle: SchemaBundle, context: dict[str, Any]) -> dict[str, Any]:
    model: dict[str, Any] = {}
    for field in bundle.mapping["fields"]:
        set_path(model, field["target"], _evaluate(field["value"], context))
    return model


def render_bundle(bundle: SchemaBundle, model: dict[str, Any]) -> str:
    template = Environment(undefined=StrictUndefined).from_string(
        bundle.template_path.read_text(encoding="utf-8")
    )
    rendered = template.render(model=model)
    return rendered.rstrip() + "\n"


def render_output_filename(bundle: SchemaBundle, context: dict[str, Any]) -> str:
    filename = Environment(undefined=StrictUndefined).from_string(
        bundle.output_filename
    ).render(context=context)
    path = Path(filename)
    if path.name != filename or not filename.endswith(".md"):
        raise ValueError("Bundle output_filename must be an .md filename, not a path")
    return filename


def validate_model(bundle: SchemaBundle, model: dict[str, Any]) -> list[tuple[str, str]]:
    root = bundle.schema["classes"][bundle.manifest["root_class"]]
    findings: list[tuple[str, str]] = []
    _validate_object(model, root, bundle.schema, "", findings)
    return findings


def collect_bundle_answers(
    bundle: SchemaBundle, findings: list[tuple[str, str]], answers: dict[str, Any]
) -> dict[str, Any]:
    if not sys.stdin.isatty():
        return answers
    fields = {field["target"]: field for field in bundle.mapping["fields"]}
    for target, message in findings:
        field = fields.get(target)
        source = _answer_source(field and field["value"])
        if not source or not source.startswith("answers."):
            continue
        value = questionary.text(field.get("prompt", f"{target}: {message}")).ask()
        if value is None:
            continue
        set_path(answers, source.removeprefix("answers."), parse_user_value(value))
    return answers


def _evaluate(spec: Any, context: dict[str, Any]) -> Any:
    if not isinstance(spec, dict):
        return spec
    if "constant" in spec:
        return spec["constant"]
    if "template" in spec:
        return Environment(undefined=StrictUndefined).from_string(spec["template"]).render(
            **context
        )
    if "list" in spec:
        return [_evaluate(value, context) for value in spec["list"]]
    if "items" in spec:
        values = _get_source(context, spec["source"]) or []
        return [_evaluate(spec["items"], context | {"item": item}) for item in values]
    if "source" in spec:
        value = _get_source(context, spec["source"])
        if "default" in spec and value in (None, ""):
            value = spec["default"]
        if "lookup" in spec:
            value = spec["lookup"].get(str(value), spec.get("default"))
        return value
    if "first" in spec:
        for value_spec in spec["first"]:
            value = _evaluate(value_spec, context)
            if not is_missing(value):
                return value
        return None
    if "object" in spec:
        return {key: _evaluate(value, context) for key, value in spec["object"].items()}
    raise ValueError(f"Unsupported mapping expression: {spec}")


def _get_source(context: dict[str, Any], path: str) -> Any:
    root, _, child_path = path.partition(".")
    value = context.get(root)
    if child_path and isinstance(value, dict) and child_path in value:
        return value[child_path]
    return get_path(context, path)


def _answer_source(spec: Any) -> str | None:
    if not isinstance(spec, dict):
        return None
    source = spec.get("source")
    if isinstance(source, str) and source.startswith("answers."):
        return source
    for candidate in spec.get("first", []):
        source = _answer_source(candidate)
        if source:
            return source
    return None


def _validate_object(
    value: Any,
    definition: dict[str, Any],
    schema: dict[str, Any],
    prefix: str,
    findings: list[tuple[str, str]],
) -> None:
    attributes = definition.get("attributes", {})
    for name, rule in attributes.items():
        path = f"{prefix}.{name}".strip(".")
        field_value = value.get(name) if isinstance(value, dict) else None
        required = rule.get("required") or _condition_matches(
            rule.get("required_if"), value
        )
        if required and is_missing(field_value):
            findings.append((path, "required value is missing"))
            continue
        if field_value is None:
            continue
        if rule.get("multivalued") and not isinstance(field_value, list):
            findings.append((path, "expected a list"))
            continue
        values = field_value if rule.get("multivalued") else [field_value]
        for item in values:
            enum = schema.get("enums", {}).get(rule.get("range"), {})
            allowed = enum.get("permissible_values", {})
            if allowed and item not in allowed:
                findings.append((path, f"expected one of {sorted(allowed)}"))
            nested = schema.get("classes", {}).get(rule.get("range"))
            if nested:
                if not isinstance(item, dict):
                    findings.append((path, "expected an object"))
                else:
                    _validate_object(item, nested, schema, path, findings)
            message = _scalar_error(item, rule)
            if message:
                findings.append((path, message))


def _condition_matches(condition: Any, value: Any) -> bool:
    if not isinstance(condition, dict):
        return False
    return all(get_path(value, path) == expected for path, expected in condition.items())


def _scalar_error(value: Any, rule: dict[str, Any]) -> str | None:
    value_range = rule.get("range")
    valid_type = {
        "string": lambda item: isinstance(item, str),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "float": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        "double": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        "boolean": lambda item: isinstance(item, bool),
        "date": lambda item: _is_date(item),
        "uri": lambda item: isinstance(item, str) and bool(urlparse(item).scheme),
    }
    if value_range in valid_type and not valid_type[value_range](value):
        return f"expected {value_range}"
    pattern = rule.get("pattern")
    if pattern and (not isinstance(value, str) or not re.fullmatch(pattern, value)):
        return f"must match {pattern!r}"
    return None


def _is_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping")
    return data
