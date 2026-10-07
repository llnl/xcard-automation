from __future__ import annotations

from typing import Any

from .utils import dump_yaml


def render_datacard(metadata: dict[str, Any]) -> str:
    frontmatter = dump_yaml(metadata).strip()
    body = render_body(metadata)
    return f"---\n{frontmatter}\n---\n\n{body}".rstrip() + "\n"


def render_body(metadata: dict[str, Any]) -> str:
    lines: list[str] = []
    name = metadata["identification"]["name"]
    lines.append(f"# Datacard for {name}")
    lines.append(f"**Last Updated**: {metadata['datacard']['updated_date']}")
    lines.append("")
    lines.append(f"**Dataset Readiness Level:** {metadata['dataset_readiness']['level']}")
    lines.append("")
    lines.append("### Machine Usability Snapshot")
    lines.append("| Aspect | Status |")
    lines.append("|--------|--------|")
    lines.append(f"| AI Ready | {_status_word(metadata['ai_usage'].get('ai_ready'))} |")
    lines.append(f"| License Clarity | {'Yes' if metadata['license'].get('spdx_id') not in {'', 'pending'} else 'No'} |")
    lines.append(f"| Machine Access | {'Yes' if metadata['access'].get('current_location') else 'No'} |")
    lines.append(f"| Checksum / Fixity | {'Yes' if metadata['integrity'].get('checksum_available') else 'No'} |")
    lines.append(f"| Semantic Context | {'Yes' if metadata['semantic_layer'].get('schema_url') or metadata['semantic_layer'].get('semantic_context') else 'No'} |")
    lines.append("")
    lines.append("# ---- Level 1: Discoverable ----")
    lines.append("---")
    lines.append("## Identification")
    lines.append("")
    lines.append("### Files & Structure")
    lines.append(_files_and_structure(metadata))
    lines.append("")
    lines.append("---")
    lines.append("## Description")
    lines.append("")
    lines.append("### Dataset Description [required]")
    lines.append(metadata["description"]["summary"])
    lines.append("")
    lines.append("### Keywords [strongly recommended]")
    lines.append(", ".join(metadata["description"]["keywords"]) or "Not provided")
    lines.append("")
    lines.append("### Citation")
    lines.append(_code_or_text(metadata["citation"]["preferred_citation"]))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("# ---- Level 2: Interoperable and Reusable ----")
    lines.append("")
    lines.append("### Sharing & Access")
    lines.append(_sharing_access(metadata))
    lines.append("")
    lines.append("### Security / Marking Considerations")
    lines.append(_security_summary(metadata))
    lines.append("")
    lines.append("---")
    lines.append("### Access and Permissions")
    lines.append(_permissions_summary(metadata))
    lines.append("")
    lines.append("### Access conditions")
    lines.append(_access_conditions(metadata))
    lines.append("")
    lines.append("### Release review process")
    lines.append(_review_process(metadata))
    lines.append("")
    lines.append("---")
    lines.append("## Context")
    lines.append("")
    lines.append("### Domain and Purpose")
    lines.append(_domain_and_purpose(metadata))
    lines.append("")
    lines.append("### Resources used, including funding and facilities, to create the dataset")
    lines.append(_resources_summary(metadata))
    lines.append("")
    lines.append("---")
    lines.append("## Provenance")
    lines.append("")
    lines.append("### Developed by")
    lines.append(_people_list(metadata["authors"]))
    lines.append("")
    lines.append("### Contributed by")
    lines.append(_people_list(metadata["contributors"]))
    lines.append("")
    lines.append("---")
    lines.append("## Related Resources")
    lines.append("")
    lines.append("### Related datasets, standards, metadata, and ontologies")
    lines.append(_related_resources(metadata["related_resources"]["datasets"]))
    lines.append("")
    lines.append("### Related publications")
    lines.append(_related_resources(metadata["related_resources"]["publications"]))
    lines.append("")
    lines.append("### Related software")
    lines.append(_related_resources(metadata["related_resources"]["software"]))
    lines.append("")
    lines.append("### Related ai model")
    lines.append(_related_resources(metadata["related_resources"]["ai_models"]))
    lines.append("")
    lines.append("---")
    lines.append("## Methods")
    lines.append("")
    lines.append("### Dataset generation, collection, and procedures")
    lines.append(_methods_summary(metadata))
    lines.append("")
    lines.append("### Maintenance & Updates")
    lines.append(_maintenance_summary(metadata))
    lines.append("")
    lines.append("# ---- Level 3: Understandable & Trustworthy ----")
    lines.append("")
    lines.append("### Data Characteristics")
    lines.append(_data_characteristics(metadata))
    lines.append("")
    lines.append("### Data Quality & Limitations")
    lines.append(_quality_summary(metadata))
    lines.append("")
    lines.append("### Related Schemas or Ontologies")
    lines.append(_semantic_summary(metadata))
    lines.append("")
    lines.append("### List of variable name(s), description(s), unit(s), and value labels for each variable in the dataset/file.")
    lines.append(_feature_table(metadata["dataset_info"]["features"]))
    lines.append("")
    lines.append("### Codes used for missing data")
    lines.append(_missing_code_table(metadata["data_quality"]["missing_data_codes"]))
    lines.append("")
    lines.append("### Specialized formats or other abbreviations used")
    lines.append(", ".join(metadata["dataset_info"]["formats"]) or "Not provided")
    lines.append("")
    lines.append("### Example of the contents")
    lines.append(_example_summary(metadata))
    lines.append("")
    lines.append("### Data Processing")
    lines.append(str(metadata["provenance"]["processing_steps"]))
    lines.append("")
    lines.append("### Software used to preprocess/ clean/ label the data")
    lines.append(_software_summary(metadata))
    lines.append("")
    lines.append("## Integrity & Versioning")
    lines.append(_integrity_summary(metadata))
    lines.append("")
    lines.append("## Semantic / Schema Information")
    lines.append(_semantic_summary(metadata))
    lines.append("")
    lines.append("## AI / Machine Learning Considerations")
    lines.append(_ai_summary(metadata))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Additional Information")
    lines.append(str(metadata["description"].get("limitations", "Not provided")))
    lines.append("")
    lines.append("---")
    return "\n".join(lines)


def _status_word(value: Any) -> str:
    if value in (True, "true", "True"):
        return "Yes"
    if value in (False, "false", "False"):
        return "No"
    if value in ("conditional", "Conditional"):
        return "Conditional"
    return "No"


def _files_and_structure(metadata: dict[str, Any]) -> str:
    formats = ", ".join(metadata["dataset_info"]["formats"]) or "unknown formats"
    splits = ", ".join(metadata["dataset_info"]["splits"]) or "no predefined splits"
    record_count = metadata["dataset_scale"]["record_count"]
    record_unit = metadata["dataset_scale"]["record_unit"]
    location = metadata["access"]["current_location"]
    return f"The dataset is stored at `{location}` and contains {record_count} {record_unit} across {formats}. Declared splits: {splits}."


def _sharing_access(metadata: dict[str, Any]) -> str:
    access_level = metadata["access_policy"]["access_level"]
    location = metadata["access"]["current_location"]
    return f"Access level is `{access_level}`. Current location: `{location}`."


def _security_summary(metadata: dict[str, Any]) -> str:
    security = metadata["security"]
    return (
        f"Classification `{security['classification']}` with dataset sensitivity `{security['sensitivity_tier']}` "
        f"and export control `{security['export_control']}`. Handling notes: {security['handling_instructions']}."
    )


def _permissions_summary(metadata: dict[str, Any]) -> str:
    policy = metadata["access_policy"]
    return f"Access level `{policy['access_level']}` with authorization requirement `{policy['authorization_required']}`."


def _access_conditions(metadata: dict[str, Any]) -> str:
    policy = metadata["access_policy"]
    if policy["access_restrictions"] not in {"", "not_applicable"}:
        return str(policy["access_restrictions"])
    return "No additional access conditions were provided."


def _review_process(metadata: dict[str, Any]) -> str:
    reviews = metadata["reviews"]
    if not reviews:
        return f"Current release status is `{metadata['release_status']}`. No formal review history provided."
    return _related_resources(reviews)


def _domain_and_purpose(metadata: dict[str, Any]) -> str:
    domain = metadata["categorization"]["science_domain"]
    purpose = metadata["description"]["purpose"]
    if purpose == "not_applicable":
        purpose = metadata["description"]["summary"]
    return f"This dataset is categorized in `{domain}` and was created to support: {purpose}"


def _resources_summary(metadata: dict[str, Any]) -> str:
    sponsors = _name_list(metadata["sponsor_organizations"])
    orgs = _name_list(metadata["research_organizations"])
    facilities = _name_list(metadata["facilities"])
    return f"Sponsors: {sponsors}. Research organizations: {orgs}. Facilities: {facilities}."


def _people_list(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "Not provided."
    lines = []
    for entry in entries:
        if entry.get("type") == "organization":
            org = entry.get("organization", {})
            lines.append(f"- {org.get('name', 'Unknown organization')} ({entry.get('role', 'unknown role')})")
            continue
        person = entry.get("person", {})
        affiliation = person.get("affiliation", {})
        role = entry.get("role", "unknown role")
        lines.append(
            f"- {person.get('given_name', '')} {person.get('family_name', '')}".strip()
            + f" — {role}; {affiliation.get('name', 'no affiliation')}; {person.get('email', 'no email')}"
        )
    return "\n".join(lines)


def _related_resources(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "Not provided."
    lines = []
    for entry in entries:
        if isinstance(entry, dict):
            parts = []
            for key in ("name", "type", "value", "version", "relationship", "purpose", "status"):
                value = entry.get(key)
                if value not in (None, "", [], {}):
                    parts.append(f"{key}={value}")
            identifier = entry.get("identifier")
            if identifier:
                parts.append(f"identifier={identifier.get('type')}:{identifier.get('value')}")
            lines.append("- " + ", ".join(parts))
        else:
            lines.append(f"- {entry}")
    return "\n".join(lines)


def _methods_summary(metadata: dict[str, Any]) -> str:
    provenance = metadata["provenance"]
    return (
        f"Generated by: {provenance['was_generated_by']}. "
        f"Collection methodology: {metadata['description']['collection_methodology']}. "
        f"Instrumentation: {provenance['instrumentation']}."
    )


def _maintenance_summary(metadata: dict[str, Any]) -> str:
    stewardship = metadata["stewardship"]
    return (
        f"Stewardship level `{stewardship['level']}` with update frequency `{stewardship['update_frequency']}`. "
        f"Versioning strategy: {stewardship['versioning_strategy']}."
    )


def _data_characteristics(metadata: dict[str, Any]) -> str:
    info = metadata["dataset_info"]
    modalities = ", ".join(info["modalities"]) if info["modalities"] else "not provided"
    splits = ", ".join(info["splits"]) if info["splits"] else "none"
    return f"Formats: {', '.join(info['formats'])}. Modalities: {modalities}. Splits: {splits}."


def _quality_summary(metadata: dict[str, Any]) -> str:
    quality = metadata["data_quality"]
    return (
        f"Completeness: {quality['completeness']}. Known issues: {quality['known_issues']}. "
        f"Validation methods: {quality['validation_methods']}. "
        f"Limitations: {metadata['description']['limitations']}."
    )


def _semantic_summary(metadata: dict[str, Any]) -> str:
    semantic = metadata["semantic_layer"]
    context = ", ".join(semantic["semantic_context"]) if semantic["semantic_context"] else "not provided"
    if not semantic["schema_url"] and context == "not provided":
        return "No formal schema or ontology was provided."
    return f"Schema URL: {semantic['schema_url'] or 'not provided'}. Semantic context: {context}."


def _feature_table(features: list[Any]) -> str:
    if not features:
        return "Not provided."
    if features and isinstance(features[0], str):
        rows = ["| Variable Name | Description | Unit | Value Labels |", "|---|---|---|---|"]
        for feature in features:
            rows.append(f"| {feature} | Not provided | not_applicable | not_applicable |")
        return "\n".join(rows)
    rows = ["| Variable Name | Description | Unit | Value Labels |", "|---|---|---|---|"]
    for feature in features:
        rows.append(
            f"| {feature.get('name', 'unknown')} | {feature.get('description', 'Not provided')} | "
            f"{feature.get('unit', 'not_applicable')} | {feature.get('range', 'not_applicable')} |"
        )
    return "\n".join(rows)


def _missing_code_table(codes: list[dict[str, Any]]) -> str:
    if not codes:
        return "No specialized missing-data codes were provided."
    rows = ["| Code | Description |", "|---|---|"]
    for code in codes:
        rows.append(f"| {code.get('code', '')} | {code.get('description', '')} |")
    return "\n".join(rows)


def _example_summary(metadata: dict[str, Any]) -> str:
    features = metadata["dataset_info"]["features"]
    if not features:
        return "No sample content was provided."
    if isinstance(features[0], str):
        return "Representative columns include: " + ", ".join(features[:5]) + "."
    return "Representative fields include: " + ", ".join(feature.get("name", "") for feature in features[:5]) + "."


def _software_summary(metadata: dict[str, Any]) -> str:
    software = metadata["related_resources"]["software"]
    env = metadata["provenance"]["software_environment"]
    pieces = []
    if software:
        pieces.append(_related_resources(software))
    if env:
        pieces.append(f"Environment notes: {env.get('notes', 'not_applicable')}.")
    return "\n".join(pieces) if pieces else "Not provided."


def _integrity_summary(metadata: dict[str, Any]) -> str:
    integrity = metadata["integrity"]
    stewardship = metadata["stewardship"]
    return (
        f"Checksums available: {integrity['checksum_available']}. "
        f"Checksum type: {integrity['checksum_type']}. "
        f"Checksum value: {integrity['checksum_value']}. "
        f"Fixity policy: {integrity['fixity_policy']}. "
        f"Versioning: {stewardship['versioning_strategy']}."
    )


def _ai_summary(metadata: dict[str, Any]) -> str:
    usage = metadata["ai_usage"]
    return (
        f"AI-ready: {_status_word(usage['ai_ready'])}. "
        f"Training: {_status_word(usage['training_use_allowed'])}. "
        f"Inference: {_status_word(usage['inference_use_allowed'])}. "
        f"Evaluation: {_status_word(usage['evaluation_use_allowed'])}. "
        f"Restrictions: {usage['restrictions']}. Bias risks: {usage['bias_risks']}. "
        f"Safety considerations: {usage['safety_considerations']}. Human review required: {usage['human_review_required']}."
    )


def _name_list(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "Not provided"
    names = []
    for entry in entries:
        if isinstance(entry, dict):
            names.append(entry.get("name", "unknown"))
        else:
            names.append(str(entry))
    return ", ".join(names)


def _code_or_text(value: str) -> str:
    if "\n" in value:
        return f"```bibtex\n{value}\n```"
    return value or "Not provided."
