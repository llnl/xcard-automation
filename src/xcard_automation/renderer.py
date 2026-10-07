from typing import Any

from .utils import dump_yaml


def render_datacard(metadata: dict[str, Any]) -> str:
    frontmatter = dump_yaml(metadata).strip()
    body = render_body(metadata)
    return f"---\n{frontmatter}\n---\n\n{body}".rstrip() + "\n"


def render_body(metadata: dict[str, Any]) -> str:

    return f"""
        # Datacard for {metadata["identification"]["name"]}
        **Last Updated**: {metadata['datacard']['updated_date']}

        **Dataset Readiness Level:** {metadata['dataset_readiness']['level']}

        "### Machine Usability Snapshot",
        "| Aspect | Status |",
        "|--------|--------|",
        | AI Ready | {_status_word(metadata['ai_usage'].get('ai_ready'))} |
        | License Clarity | {'Yes' if metadata['license'].get('spdx_id') not in {'', 'pending'} else 'No'} |
        | Machine Access | {'Yes' if metadata['access'].get('current_location') else 'No'} |
        | Checksum / Fixity | {'Yes' if metadata['integrity'].get('checksum_available') else 'No'} |
        | Semantic Context | {'Yes' if metadata['semantic_layer'].get('schema_url') or metadata['semantic_layer'].get('semantic_context') else 'No'} |

        # ---- Level 1: Discoverable ----
        ---
        ## Identification

        ### Files & Structure
        {_files_and_structure(metadata)}

        ---
        ## Description

        ### Dataset Description [required]
        {metadata["description"]["summary"]}

        ### Keywords [strongly recommended]
        {", ".join(metadata["description"]["keywords"]) or "Not provided"}

        ### Citation
        {_code_or_text(metadata["citation"]["preferred_citation"])}

        ---

        # ---- Level 2: Interoperable and Reusable ----

        ### Sharing & Access
        {_sharing_access(metadata)}

        ### Security / Marking Considerations
        {_security_summary(metadata)}

        ---
        ### Access and Permissions
        {_permissions_summary(metadata)}

        ### Access conditions
        {_access_conditions(metadata)}

        ### Release review process
        {_review_process(metadata)}

        ---
        ## Context

        ### Domain and Purpose
        {_domain_and_purpose(metadata)}

        ### Resources used, including funding and facilities, to create the dataset
        {_resources_summary(metadata)}

        ---
        ## Provenance

        ### Developed by
        {_people_list(metadata["authors"])}

        ### Contributed by
        {_people_list(metadata["contributors"])}

        ---
        ## Related Resources

        ### Related datasets, standards, metadata, and ontologies
        {_related_resources(metadata["related_resources"]["datasets"])}

        ### Related publications
        {_related_resources(metadata["related_resources"]["publications"])}

        ### Related software
        {_related_resources(metadata["related_resources"]["software"])}

        ### Related ai model
        {_related_resources(metadata["related_resources"]["ai_models"])}

        ---
        ## Methods

        ### Dataset generation, collection, and procedures
        {_methods_summary(metadata)}

        ### Maintenance & Updates
        {_maintenance_summary(metadata)}

        # ---- Level 3: Understandable & Trustworthy ----

        ### Data Characteristics
        {_data_characteristics(metadata)}

        ### Data Quality & Limitations
        {_quality_summary(metadata)}

        ### Related Schemas or Ontologies
        {_semantic_summary(metadata)}

        ### List of variable name(s), description(s), unit(s), and value labels for each variable in the dataset/file.
        {_feature_table(metadata["dataset_info"]["features"])}

        ### Codes used for missing data
        {_missing_code_table(metadata["data_quality"]["missing_data_codes"])}

        ### Specialized formats or other abbreviations used
        {", ".join(metadata["dataset_info"]["formats"]) or "Not provided"}

        ### Example of the contents
        {_example_summary(metadata)}

        ### Data Processing
        {str(metadata["provenance"]["processing_steps"])}

        ### Software used to preprocess/ clean/ label the data
        {_software_summary(metadata)}

        ## Integrity & Versioning
        {_integrity_summary(metadata)}

        ## Semantic / Schema Information
        {_semantic_summary(metadata)}

        ## AI / Machine Learning Considerations
        {_ai_summary(metadata)}

        ---

        ## Additional Information
        {str(metadata["description"].get("limitations", "Not provided"))}

        ---

    """


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
    return f"""
        Classification `{security['classification']}` with dataset sensitivity `{security['sensitivity_tier']}`.
        and export control `{security['export_control']}`. Handling notes: {security['handling_instructions']}.
    """


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
    return f"""
        Generated by: {provenance['was_generated_by']}.
        Collection methodology: {metadata['description']['collection_methodology']}.
        Instrumentation: {provenance['instrumentation']}.
    """


def _maintenance_summary(metadata: dict[str, Any]) -> str:
    stewardship = metadata["stewardship"]
    return f"""
        Stewardship level `{stewardship['level']}` with update frequency `{stewardship['update_frequency']}`.
        Versioning strategy: {stewardship['versioning_strategy']}.
    """



def _data_characteristics(metadata: dict[str, Any]) -> str:
    info = metadata["dataset_info"]
    modalities = ", ".join(info["modalities"]) if info["modalities"] else "not provided"
    splits = ", ".join(info["splits"]) if info["splits"] else "none"
    return f"Formats: {', '.join(info['formats'])}. Modalities: {modalities}. Splits: {splits}."


def _quality_summary(metadata: dict[str, Any]) -> str:
    quality = metadata["data_quality"]
    return f"""
        Completeness: {quality['completeness']}. Known issues: {quality['known_issues']}.
        Validation methods: {quality['validation_methods']}.
        Limitations: {metadata['description']['limitations']}.
    """


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
    return f"""
        Checksums available: {integrity['checksum_available']}.
        Checksum type: {integrity['checksum_type']}.
        Checksum value: {integrity['checksum_value']}.
        Fixity policy: {integrity['fixity_policy']}.
        Versioning: {stewardship['versioning_strategy']}.
    """


def _ai_summary(metadata: dict[str, Any]) -> str:
    usage = metadata["ai_usage"]
    return f"""
        AI-ready: {_status_word(usage['ai_ready'])}.
        Training: {_status_word(usage['training_use_allowed'])}.
        Inference: {_status_word(usage['inference_use_allowed'])}.
        Evaluation: {_status_word(usage['evaluation_use_allowed'])}.
        Restrictions: {usage['restrictions']}. Bias risks: {usage['bias_risks']}.
        Safety considerations: {usage['safety_considerations']}. Human review required: {usage['human_review_required']}.
    """


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
