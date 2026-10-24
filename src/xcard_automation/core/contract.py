from dataclasses import dataclass
ENUMS = {
    "datacard.profile": {"core", "extended", "ai_ready", "sensitive"},
    "datacard.sensitivity_tier": {
        "tier0_open",
        "tier1_controlled_research",
        "tier2_proprietary",
        "tier3_sensitive",
        "tier4_export_controlled",
        "tier5_regulated_personal",
        "tier6_classified",
    },
    "datacard.access_level": {"open", "restricted", "controlled"},
    "datacard.creation_method": {"manual", "automated", "hybrid"},
    "object_type": {"dataset", "model", "software", "ai_agent", "eval", "framework", "other"},
    "dataset_type": {"GD", "IM", "ND", "SM", "FP", "I", "MM", "MD", "AS", "IP", "IG"},
    "release_status": {"draft", "under_review", "approved", "published", "deprecated"},
    "workflow.state": {"raw", "processing", "qa", "analysis", "review", "embargo", "published", "archived"},
    "security.classification": {"U", "CUI", "C", "S", "TS"},
    "security.export_control": {"none", "EAR", "ITAR"},
    "access_policy.access_level": {"open", "restricted", "controlled"},
    "access_policy.authorization_required": {
        "none",
        "account",
        "user_agreement",
        "data_use_agreement",
        "sponsor_approval",
        "export_control_review",
        "irb_approval",
        "other",
    },
    "stewardship.level": {"project_managed", "repository_managed", "externally_managed"},
    "stewardship.update_frequency": {"none", "ad_hoc", "monthly", "quarterly", "annually", "other"},
}


SCIENCE_DOMAINS = {
    "materials_science",
    "biology",
    "physics",
    "chemistry",
    "climate",
    "fusion",
    "lightsource",
    "computer_science",
    "other",
}


DATASET_TYPE_BY_FORMAT = {
    "CSV": "ND",
    "TSV": "ND",
    "JSON": "ND",
    "YAML": "ND",
    "HDF5": "ND",
    "NetCDF4": "ND",
    "Parquet": "ND",
    "Arrow": "ND",
    "PNG": "IM",
    "JPEG": "IM",
    "TIFF": "IM",
    "PyTorch": "MD",
    "NumPy": "ND",
}


SPDX_LICENSE_NAMES = {
    "MIT": "MIT License",
    "Apache-2.0": "Apache License 2.0",
    "BSD-3-Clause": "BSD 3-Clause License",
    "CC-BY-4.0": "Creative Commons Attribution 4.0 International",
    "CC0-1.0": "Creative Commons Zero v1.0 Universal",
}


COMMON_REQUIRED_FIELDS = [
    "datacard.datacard_version",
    "datacard.profile",
    "datacard.filename",
    "datacard.language",
    "datacard.sensitivity_tier",
    "datacard.access_level",
    "datacard.creation_method",
    "datacard.created_date",
    "datacard.updated_date",
    "datacard.change_log",
    "datacard.created_by",
    "identification.name",
    "identification.project",
    "identification.version",
    "identification.primary_id.type",
    "identification.primary_id.value",
    "description.summary",
    "description.keywords",
    "object_type",
    "dataset_type",
    "release_status",
    "workflow.state",
    "security.classification",
    "security.sensitivity_tier",
    "security.export_control",
    "access_policy.sensitivity_tier",
    "access_policy.access_level",
    "access_policy.authorization_required",
    "contact.type",
    "sponsor_organizations",
    "research_organizations",
    "categorization.science_domain",
    "categorization.tags.project",
    "dataset_info.formats",
    "provenance.was_generated_by",
]


PROFILE_REQUIRED_FIELDS = {
    "core": [],
    "extended": [
        "license.spdx_id",
        "license.name",
        "dataset_scale.record_count",
        "dataset_scale.record_unit",
        "dataset_scale.compressed_bytes",
        "dates.data_collection_start",
        "dates.data_collection_end",
        "stewardship.level",
        "stewardship.update_frequency",
    ],
    "ai_ready": [
        "license.spdx_id",
        "license.name",
        "dataset_scale.record_count",
        "dataset_scale.record_unit",
        "dataset_scale.compressed_bytes",
        "dates.data_collection_start",
        "dates.data_collection_end",
        "ai_usage.ai_ready",
        "ai_usage.training_use_allowed",
        "ai_usage.inference_use_allowed",
        "ai_usage.evaluation_use_allowed",
        "ai_usage.human_review_required",
        "data_quality.completeness",
        "data_quality.known_issues",
        "data_quality.validation_methods",
        "integrity.checksum_available",
        "semantic_layer.schema_url",
    ],
    "sensitive": [
        "license.spdx_id",
        "license.name",
        "dataset_scale.record_count",
        "dataset_scale.record_unit",
        "dataset_scale.compressed_bytes",
        "dates.data_collection_start",
        "dates.data_collection_end",
        "compliance.export_control_reviewed",
        "compliance.irb_approved",
        "compliance.security_review_completed",
    ],
}


CONDITIONAL_FIELDS = {
    "published": [
        "citation.preferred_citation",
        "authors",
    ],
    "classified": [
        "security.classification_reason",
        "security.declassification.review_date",
        "security.declassification.authority",
    ],
    "export_controlled": ["security.export_control_id"],
    "contains_pii": ["security.pii.types"],
    "checksums_present": ["integrity.checksum_type", "integrity.checksum_value"],
}


@dataclass(frozen=True)
class PromptField:
    path: str
    prompt: str


PROMPT_BATCHES = [
    [
        PromptField("identification.project", "Project or sub-project for this dataset"),
        PromptField("categorization.science_domain", "Science domain (e.g. materials_science, physics, fusion)"),
        PromptField("contact.person.given_name", "Primary contact given name"),
    ],
    [
        PromptField("contact.person.family_name", "Primary contact family name"),
        PromptField("contact.person.email", "Primary contact email"),
        PromptField("sponsor_organizations", "Sponsor organizations as YAML list of objects"),
    ],
    [
        PromptField("research_organizations", "Research organizations as YAML list of objects"),
        PromptField("provenance.was_generated_by", "High-level dataset generation description"),
        PromptField("description.summary", "Plain-language dataset summary"),
    ],
    [
        PromptField("license.spdx_id", "SPDX license identifier"),
        PromptField("license.name", "Human-readable license name"),
        PromptField("dates.data_collection_start", "Collection start date (YYYY-MM-DD)"),
    ],
    [
        PromptField("dates.data_collection_end", "Collection end date (YYYY-MM-DD)"),
        PromptField("stewardship.level", "Stewardship level"),
        PromptField("stewardship.update_frequency", "Update frequency"),
    ],
    [
        PromptField("ai_usage.ai_ready", "AI-ready flag: true, false, or conditional"),
        PromptField("ai_usage.training_use_allowed", "Training use allowed: true, false, or conditional"),
        PromptField("ai_usage.inference_use_allowed", "Inference use allowed: true, false, or conditional"),
    ],
    [
        PromptField("ai_usage.evaluation_use_allowed", "Evaluation use allowed: true, false, or conditional"),
        PromptField("ai_usage.human_review_required", "Human review required: true or false"),
        PromptField("data_quality.completeness", "Data completeness notes"),
    ],
    [
        PromptField("data_quality.known_issues", "Known issues"),
        PromptField("data_quality.validation_methods", "Validation methods"),
        PromptField("semantic_layer.schema_url", "Formal schema URL"),
    ],
    [
        PromptField("compliance.export_control_reviewed", "Export control reviewed: true or false"),
        PromptField("compliance.irb_approved", "IRB approved: true, false, or not_applicable"),
        PromptField("compliance.security_review_completed", "Security review completed: true or false"),
    ],
]


def required_fields(profile: str, metadata: dict) -> list[str]:
    fields = list(COMMON_REQUIRED_FIELDS)
    fields.extend(PROFILE_REQUIRED_FIELDS.get(profile, []))

    release_status = metadata.get("release_status")
    if release_status in {"approved", "published"}:
        fields.extend(CONDITIONAL_FIELDS["published"])

    classification = metadata.get("security", {}).get("classification")
    if classification and classification != "U":
        fields.extend(CONDITIONAL_FIELDS["classified"])

    export_control = metadata.get("security", {}).get("export_control")
    if export_control and export_control != "none":
        fields.extend(CONDITIONAL_FIELDS["export_controlled"])

    pii_present = metadata.get("security", {}).get("pii", {}).get("present")
    if pii_present is True:
        fields.extend(CONDITIONAL_FIELDS["contains_pii"])

    checksum_available = metadata.get("integrity", {}).get("checksum_available")
    if checksum_available is True:
        fields.extend(CONDITIONAL_FIELDS["checksums_present"])

    return list(dict.fromkeys(fields))
