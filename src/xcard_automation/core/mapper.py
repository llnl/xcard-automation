from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
from typing import Any

from .contract import DATASET_TYPE_BY_FORMAT, SPDX_LICENSE_NAMES
from .utils import flatten_answers, set_path, snake_case, today_iso


def build_metadata(
    dataset_dir: Path,
    profile: str,
    introspection: dict[str, Any],
    answers: dict[str, Any],
    checksum_info: dict[str, Any] | None = None,
    resume_created_date: str | None = None,
) -> dict[str, Any]:
    answers = flatten_answers(answers)
    title = (
        answers.get("identification.name")
        or introspection.get("citation", {}).get("title")
        or introspection.get("readme_title")
        or dataset_dir.name.replace("_", " ").title()
    )
    dataset_slug = snake_case(title)
    today = today_iso()
    created_date = answers.get("datacard.created_date") or resume_created_date or today
    updated_date = today
    keywords = (
        answers.get("description.keywords")
        or introspection.get("citation", {}).get("keywords")
        or introspection.get("readme_keywords")
        or ["dataset"]
    )
    formats = introspection.get("formats") or ["Text"]
    dataset_type = answers.get("dataset_type") or _infer_dataset_type(formats)
    contact_type = answers.get("contact.type", "person")
    datacard_doc_access = answers.get("datacard.access_level", "open")
    dataset_sensitivity = answers.get("security.sensitivity_tier", "tier0_open")
    release_status = answers.get("release_status", "draft")
    description_summary = (
        answers.get("description.summary")
        or introspection.get("readme_summary")
        or f"Dataset located at {dataset_dir}."
    )
    metadata: dict[str, Any] = {
        "datacard": {
            "template_version": "0.1",
            "datacard_version": "1.0",
            "profile": profile,
            "filename": f"genesis_datacard_{dataset_slug}.md",
            "language": "en",
            "sensitivity_tier": answers.get("datacard.sensitivity_tier", "tier0_open"),
            "access_level": datacard_doc_access,
            "creation_method": answers.get("datacard.creation_method", "hybrid"),
            "created_date": created_date,
            "updated_date": updated_date,
            "change_log": answers.get(
                "datacard.change_log",
                [
                    {
                        "date": updated_date,
                        "datacard_version": "1.0",
                        "summary": "Initial creation",
                    }
                ],
            ),
            "created_by": answers.get(
                "datacard.created_by",
                [
                    {
                        "role": "initial_creation",
                        "date": updated_date,
                        "description": "Automated datacard generation pipeline",
                        "creator": {
                            "type": "software",
                            "software": {
                                "name": "datacard-pipeline",
                                "version": "0.1.0",
                                "identifier": {"type": "local", "value": "datacard-pipeline"},
                            },
                        },
                    }
                ],
            ),
            "id": answers.get(
                "datacard.id",
                {"type": "local", "value": f"datacard:{dataset_slug}"},
            ),
        },
        "identification": {
            "name": title,
            "project": answers.get("identification.project", ""),
            "version": answers.get("identification.version") or introspection.get("citation", {}).get("version") or "1.0",
            "primary_id": answers.get(
                "identification.primary_id",
                _default_primary_id(dataset_slug, introspection),
            ),
            "additional_ids": answers.get("identification.additional_ids", []),
            "supersedes": answers.get("identification.supersedes"),
            "superseded_by": answers.get("identification.superseded_by"),
            "parent_collection": answers.get("identification.parent_collection"),
        },
        "description": {
            "summary": description_summary,
            "purpose": answers.get("description.purpose", "not_applicable"),
            "collection_methodology": answers.get("description.collection_methodology", "not_applicable"),
            "data_characteristics": answers.get("description.data_characteristics", "not_applicable"),
            "intended_use": answers.get("description.intended_use", "not_applicable"),
            "current_use": answers.get("description.current_use", "not_applicable"),
            "out_of_scope_use": answers.get("description.out_of_scope_use", "not_applicable"),
            "limitations": answers.get("description.limitations", "not_applicable"),
            "keywords": _ensure_list(keywords),
        },
        "object_type": answers.get("object_type", "dataset"),
        "dataset_type": dataset_type,
        "release_status": release_status,
        "workflow": {
            "state": answers.get("workflow.state", _default_workflow_state(release_status)),
            "is_intermediate": answers.get("workflow.is_intermediate", False),
            "pipeline_stage": answers.get("workflow.pipeline_stage", "not_applicable"),
            "embargo_until": answers.get("workflow.embargo_until", "not_applicable"),
        },
        "dataset_readiness": {
            "level": answers.get("dataset_readiness.level", _readiness_level(profile)),
            "evaluated_against": answers.get("dataset_readiness.evaluated_against", "Genesis Dataset Readiness Model v1.0"),
            "evaluated_at": answers.get("dataset_readiness.evaluated_at", updated_date),
            "evaluated_by": answers.get("dataset_readiness.evaluated_by", {"type": "organization", "organization": {"name": "datacard-pipeline"}}),
            "confidence": answers.get("dataset_readiness.confidence", "medium"),
        },
        "security": {
            "classification": answers.get("security.classification", "U"),
            "sensitivity_tier": dataset_sensitivity,
            "sensitivity_level": answers.get("security.sensitivity_level", "public" if dataset_sensitivity == "tier0_open" else "restricted"),
            "cui_marking": answers.get("security.cui_marking", "not_applicable"),
            "distribution_statement": answers.get("security.distribution_statement", "not_applicable"),
            "handling_instructions": answers.get("security.handling_instructions", "not_applicable"),
            "export_control": answers.get("security.export_control", "none"),
            "export_control_id": answers.get("security.export_control_id", "not_applicable"),
            "data_rights": answers.get("security.data_rights", "not_applicable"),
            "last_reviewed_date": answers.get("security.last_reviewed_date", updated_date),
            "pii": answers.get(
                "security.pii",
                {
                    "present": False,
                    "types": [],
                    "deidentification_applied": False,
                    "deidentification_method": "not_applicable",
                    "deidentification_reviewed": False,
                },
            ),
            "classification_reason": answers.get("security.classification_reason", "not_applicable"),
            "declassification": answers.get(
                "security.declassification",
                {"review_date": "not_applicable", "authority": "not_applicable"},
            ),
        },
        "access_policy": {
            "sensitivity_tier": answers.get("access_policy.sensitivity_tier", dataset_sensitivity),
            "access_level": answers.get("access_policy.access_level", "open" if dataset_sensitivity == "tier0_open" else "restricted"),
            "access_restrictions": answers.get("access_policy.access_restrictions", "not_applicable"),
            "authorization_required": answers.get("access_policy.authorization_required", "none"),
            "policy_url": answers.get("access_policy.policy_url", "not_applicable"),
            "policy_text": answers.get("access_policy.policy_text", "not_applicable"),
        },
        "license": {
            "spdx_id": answers.get("license.spdx_id", introspection.get("license_guess") or "pending"),
            "name": answers.get("license.name", SPDX_LICENSE_NAMES.get(answers.get("license.spdx_id", introspection.get("license_guess", "")), "")),
            "url": answers.get("license.url", introspection.get("license_file") or "not_applicable"),
        },
        "additional_licenses": answers.get("additional_licenses", []),
        "contact": {
            "type": contact_type,
            "person": {
                "given_name": answers.get("contact.person.given_name", ""),
                "family_name": answers.get("contact.person.family_name", ""),
                "orcid": answers.get("contact.person.orcid", "not_applicable"),
                "email": answers.get("contact.person.email", ""),
                "affiliation": {
                    "name": answers.get("contact.person.affiliation.name", "not_applicable"),
                    "ror_id": answers.get("contact.person.affiliation.ror_id", "not_applicable"),
                },
            },
            "organization": {
                "name": answers.get("contact.organization.name", "not_applicable"),
                "ror_id": answers.get("contact.organization.ror_id", "not_applicable"),
            },
            "valid_until": answers.get("contact.valid_until", "not_applicable"),
            "succession_note": answers.get("contact.succession_note", "not_applicable"),
        },
        "additional_contacts": answers.get("additional_contacts", []),
        "authors": answers.get("authors", _authors_from_introspection(introspection)),
        "contributors": answers.get("contributors", []),
        "sponsor_organizations": answers.get("sponsor_organizations", []),
        "research_organizations": answers.get("research_organizations", []),
        "facilities": answers.get("facilities", []),
        "categorization": {
            "science_domain": answers.get("categorization.science_domain", "other"),
            "tags": {
                "project": answers.get("categorization.tags.project", answers.get("identification.project", "")),
                "science": answers.get("categorization.tags.science", "not_applicable"),
                "type": answers.get("categorization.tags.type", answers.get("object_type", "dataset")),
                "risk": answers.get("categorization.tags.risk", "general"),
            },
            "task_category": answers.get("categorization.task_category", []),
            "task_subcategory": answers.get("categorization.task_subcategory", []),
        },
        "dataset_info": {
            "formats": formats,
            "encoding": answers.get("dataset_info.encoding", _default_encoding(formats)),
            "schema_version": answers.get("dataset_info.schema_version", "not_applicable"),
            "modalities": answers.get("dataset_info.modalities", _default_modalities(formats)),
            "features": answers.get("dataset_info.features", _default_features(profile, introspection)),
            "splits": answers.get("dataset_info.splits", introspection.get("splits_detected", [])),
            "language": answers.get("dataset_info.language", "not_applicable"),
            "spatial_coverage": answers.get("dataset_info.spatial_coverage", {"description": "not_applicable"}),
            "temporal_coverage": answers.get("dataset_info.temporal_coverage", {"description": "not_applicable"}),
        },
        "dataset_scale": {
            "record_count": answers.get("dataset_scale.record_count", _default_record_count(introspection)),
            "record_unit": answers.get("dataset_scale.record_unit", _default_record_unit(introspection)),
            "compressed_bytes": answers.get("dataset_scale.compressed_bytes", introspection.get("total_bytes", 0)),
            "uncompressed_bytes": answers.get("dataset_scale.uncompressed_bytes", introspection.get("total_bytes", 0)),
        },
        "dates": {
            "data_collection_start": answers.get("dates.data_collection_start", ""),
            "data_collection_end": answers.get("dates.data_collection_end", ""),
            "issued": answers.get("dates.issued", "not_applicable"),
            "modified": answers.get("dates.modified", updated_date),
        },
        "access": {
            "current_location": answers.get("access.current_location", str(dataset_dir.resolve())),
            "intended_repositories": answers.get("access.intended_repositories", []),
        },
        "provenance": {
            "was_generated_by": answers.get("provenance.was_generated_by", ""),
            "source_data": answers.get("provenance.source_data", []),
            "processing_steps": answers.get("provenance.processing_steps", "not_applicable"),
            "instrumentation": answers.get("provenance.instrumentation", "not_applicable"),
            "simulation_details": answers.get("provenance.simulation_details", "not_applicable"),
            "software_environment": answers.get(
                "provenance.software_environment",
                {
                    "os": "not_applicable",
                    "compiler": "not_applicable",
                    "container": "not_applicable",
                    "hpc_environment": "not_applicable",
                    "notes": "not_applicable",
                },
            ),
        },
        "stewardship": {
            "level": answers.get("stewardship.level", ""),
            "maintainer": answers.get(
                "stewardship.maintainer",
                {
                    "type": "person",
                    "person": {
                        "given_name": answers.get("contact.person.given_name", ""),
                        "family_name": answers.get("contact.person.family_name", ""),
                        "orcid": answers.get("contact.person.orcid", "not_applicable"),
                        "email": answers.get("contact.person.email", ""),
                        "affiliation": {
                            "name": answers.get("contact.person.affiliation.name", "not_applicable"),
                            "ror_id": answers.get("contact.person.affiliation.ror_id", "not_applicable"),
                        },
                    },
                    "organization": {"name": "not_applicable", "ror_id": "not_applicable"},
                },
            ),
            "update_frequency": answers.get("stewardship.update_frequency", ""),
            "retention_policy": answers.get("stewardship.retention_policy", "not_applicable"),
            "versioning_strategy": answers.get("stewardship.versioning_strategy", "Semantic versioning"),
        },
        "reviews": answers.get("reviews", []),
        "related_resources": {
            "datasets": answers.get("related_resources.datasets", []),
            "publications": answers.get("related_resources.publications", []),
            "software": answers.get("related_resources.software", []),
            "ai_models": answers.get("related_resources.ai_models", []),
        },
        "compliance": {
            "doe_data_management_plan": answers.get("compliance.doe_data_management_plan", False),
            "osti_elink2_metadata_compliant": answers.get("compliance.osti_elink2_metadata_compliant", False),
            "export_control_reviewed": answers.get("compliance.export_control_reviewed", False),
            "irb_approved": answers.get("compliance.irb_approved", "not_applicable"),
            "security_review_completed": answers.get("compliance.security_review_completed", False),
        },
        "citation": {
            "report_number": answers.get("citation.report_number", "not_applicable"),
            "preferred_citation": answers.get("citation.preferred_citation", _default_citation(title, introspection, answers)),
        },
        "ai_usage": {
            "ai_ready": answers.get("ai_usage.ai_ready", False if profile != "ai_ready" else ""),
            "training_use_allowed": answers.get("ai_usage.training_use_allowed", False if profile != "ai_ready" else ""),
            "inference_use_allowed": answers.get("ai_usage.inference_use_allowed", False if profile != "ai_ready" else ""),
            "evaluation_use_allowed": answers.get("ai_usage.evaluation_use_allowed", False if profile != "ai_ready" else ""),
            "restrictions": answers.get("ai_usage.restrictions", "not_applicable"),
            "bias_risks": answers.get("ai_usage.bias_risks", "not_applicable"),
            "safety_considerations": answers.get("ai_usage.safety_considerations", "not_applicable"),
            "human_review_required": answers.get("ai_usage.human_review_required", False if profile != "ai_ready" else ""),
        },
        "data_quality": {
            "completeness": answers.get("data_quality.completeness", ""),
            "known_issues": answers.get("data_quality.known_issues", ""),
            "validation_methods": answers.get("data_quality.validation_methods", ""),
            "noise_characteristics": answers.get("data_quality.noise_characteristics", "not_applicable"),
            "uncertainty_notes": answers.get("data_quality.uncertainty_notes", "not_applicable"),
            "missing_data_codes": answers.get("data_quality.missing_data_codes", []),
        },
        "integrity": {
            "checksum_available": answers.get("integrity.checksum_available", bool(checksum_info and profile == "ai_ready")),
            "checksum_type": answers.get("integrity.checksum_type", checksum_info["type"] if checksum_info and profile == "ai_ready" else "not_applicable"),
            "checksum_value": answers.get("integrity.checksum_value", checksum_info["manifest_path"] if checksum_info and profile == "ai_ready" else "not_applicable"),
            "fixity_policy": answers.get("integrity.fixity_policy", "not_applicable"),
        },
        "semantic_layer": {
            "schema_url": answers.get("semantic_layer.schema_url", ""),
            "semantic_context": answers.get("semantic_layer.semantic_context", []),
        },
        "_repository": {
            "populated_by_repository": True,
            "ingest_date": None,
            "repository_catalog_id": None,
            "completeness_score": None,
            "datacard_checksum": {"type": None, "value": None},
            "repositories": [],
            "usage_metrics": {
                "download_count": None,
                "view_count": None,
                "citation_count": None,
                "last_accessed": None,
            },
            "distributions": [],
            "data_services": [],
        },
    }

    for path, value in answers.items():
        set_path(metadata, path, value)

    metadata["datacard"]["filename"] = f"genesis_datacard_{snake_case(metadata['identification']['name'])}.md"
    metadata["categorization"]["tags"]["project"] = metadata["categorization"]["tags"]["project"] or metadata["identification"]["project"]
    if not metadata["license"]["name"]:
        metadata["license"]["name"] = SPDX_LICENSE_NAMES.get(metadata["license"]["spdx_id"], "")
    return metadata


def _default_primary_id(dataset_slug: str, introspection: dict[str, Any]) -> dict[str, str]:
    doi = introspection.get("citation", {}).get("doi")
    if doi:
        return {"type": "doi", "value": doi}
    return {"type": "local", "value": f"dataset:{dataset_slug}"}


def _infer_dataset_type(formats: list[str]) -> str:
    for file_format in formats:
        if file_format in DATASET_TYPE_BY_FORMAT:
            return DATASET_TYPE_BY_FORMAT[file_format]
    return "ND"


def _default_workflow_state(release_status: str) -> str:
    return {
        "draft": "raw",
        "under_review": "review",
        "approved": "review",
        "published": "published",
        "deprecated": "archived",
    }.get(release_status, "raw")


def _readiness_level(profile: str) -> int:
    return {"core": 1, "extended": 2, "ai_ready": 3, "sensitive": 2}[profile]


def _ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _default_encoding(formats: list[str]) -> str:
    if any(file_format in {"CSV", "TSV", "JSON", "YAML", "Text", "Markdown"} for file_format in formats):
        return "UTF-8"
    return "not_applicable"


def _default_modalities(formats: list[str]) -> list[str]:
    modalities = []
    if any(file_format in {"CSV", "TSV", "JSON", "YAML", "Parquet", "Arrow"} for file_format in formats):
        modalities.append("tabular")
    if any(file_format in {"PNG", "JPEG", "TIFF"} for file_format in formats):
        modalities.append("image")
    if any(file_format in {"Text", "Markdown"} for file_format in formats):
        modalities.append("text")
    if any(file_format in {"HDF5", "NetCDF4"} for file_format in formats):
        modalities.append("time-series")
    return modalities or ["tabular"]


def _default_features(profile: str, introspection: dict[str, Any]) -> list[Any]:
    sample_columns = introspection.get("sample_columns", {})
    if not sample_columns:
        return []
    first_columns = next(iter(sample_columns.values()))
    if profile == "ai_ready":
        return [
            {
                "name": column,
                "type": "other",
                "unit": "not_applicable",
                "description": f"Feature derived from dataset column `{column}`",
                "range": "not_applicable",
            }
            for column in first_columns
        ]
    return first_columns


def _default_record_count(introspection: dict[str, Any]) -> int:
    csv_row_counts = introspection.get("csv_row_counts", {})
    if csv_row_counts:
        return int(next(iter(csv_row_counts.values())))
    return introspection.get("file_count", 0)


def _default_record_unit(introspection: dict[str, Any]) -> str:
    return "records" if introspection.get("csv_row_counts") else "files"


def _authors_from_introspection(introspection: dict[str, Any]) -> list[dict[str, Any]]:
    authors = []
    for author in introspection.get("citation", {}).get("authors", []):
        authors.append(
            {
                "type": "person",
                "person": {
                    "given_name": author.get("given_name", ""),
                    "family_name": author.get("family_name", ""),
                    "orcid": author.get("orcid", "not_applicable"),
                    "email": author.get("email", "not_applicable"),
                    "affiliation": {
                        "name": author.get("affiliation_name", "not_applicable"),
                        "ror_id": "not_applicable",
                    },
                },
                "organization": {"name": "not_applicable", "ror_id": "not_applicable"},
                "role": "creator",
            }
        )
    return authors


def _default_citation(title: str, introspection: dict[str, Any], answers: dict[str, Any]) -> str:
    author_names = []
    for author in introspection.get("citation", {}).get("authors", []):
        pieces = [author.get("family_name", ""), author.get("given_name", "")]
        author_names.append(", ".join(piece for piece in pieces if piece))
    author_value = " and ".join(filter(None, author_names)) or "Unknown"
    year = today_iso().split("-")[0]
    doi = introspection.get("citation", {}).get("doi", "not_applicable")
    publisher = answers.get("citation.publisher", "Genesis")
    url = answers.get("citation.url", "not_applicable")
    key = snake_case(title) or "dataset"
    return "\n".join(
        [
            f"@dataset{{{key},",
            f"  author    = {{{author_value}}},",
            f"  title     = {{{title}}},",
            f"  year      = {{{year}}},",
            f"  publisher = {{{publisher}}},",
            f"  doi       = {{{doi}}},",
            f"  url       = {{{url}}}",
            "}",
        ]
    )
