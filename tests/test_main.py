"""Test for main entry point."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def write_answers(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class PipelineTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", "-m", "datacard_pipeline.cli", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

    def test_core_pipeline_generates_validated_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "runs"
            answers = Path(tmpdir) / "answers.yaml"
            write_answers(
                answers,
                {
                    "identification.project": "genesis-materials",
                    "categorization.science_domain": "materials_science",
                    "contact.person.given_name": "Ada",
                    "contact.person.family_name": "Lovelace",
                    "contact.person.email": "ada@example.org",
                    "sponsor_organizations": [{"name": "DOE Office of Science", "ror_id": "not_applicable"}],
                    "research_organizations": [{"name": "Oak Ridge National Laboratory", "ror_id": "not_applicable"}],
                    "provenance.was_generated_by": "Laboratory acquisition pipeline",
                },
            )
            result = self.run_cli(
                "run",
                str(FIXTURES / "core_dataset"),
                "--profile",
                "core",
                "--output-root",
                str(output_root),
                "--answers",
                str(answers),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            card = next(output_root.glob("core_dataset/validation_output/*.md"))
            self.assertIn("Datacard for Core Dataset", card.read_text(encoding="utf-8"))
            ontology_summary = output_root / "core_dataset" / "input" / "ontology_summary.json"
            ontology_alignment = output_root / "core_dataset" / "automation_output" / "ontology_alignment.json"
            self.assertTrue(ontology_summary.exists())
            self.assertTrue(ontology_alignment.exists())

    def test_extended_pipeline_requires_and_renders_license_fields(
        self
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "runs"
            answers = Path(tmpdir) / "answers.yaml"
            write_answers(
                answers,
                {
                    "identification.project": "genesis-fusion",
                    "categorization.science_domain": "fusion",
                    "contact.person.given_name": "Grace",
                    "contact.person.family_name": "Hopper",
                    "contact.person.email": "grace@example.org",
                    "sponsor_organizations": [{"name": "DOE", "ror_id": "not_applicable"}],
                    "research_organizations": [{"name": "Princeton Plasma Physics Laboratory", "ror_id": "not_applicable"}],
                    "provenance.was_generated_by": "Diagnostic export from fusion campaign",
                    "license.spdx_id": "MIT",
                    "license.name": "MIT License",
                    "dates.data_collection_start": "2024-01-01",
                    "dates.data_collection_end": "2024-01-31",
                    "stewardship.level": "project_managed",
                    "stewardship.update_frequency": "monthly",
                },
            )
            result = self.run_cli(
                "run",
                str(FIXTURES / "extended_dataset"),
                "--profile",
                "extended",
                "--output-root",
                str(output_root),
                "--answers",
                str(answers),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            card = next(output_root.glob("extended_dataset/validation_output/*.md"))
            text = card.read_text(encoding="utf-8")
            self.assertIn("MIT License", text)
            self.assertIn("Fusion Diagnostic Dataset", text)

    def test_ai_ready_pipeline_writes_checksum_and_feature_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "runs"
            answers = Path(tmpdir) / "answers.yaml"
            write_answers(
                answers,
                {
                    "identification.project": "genesis-ai",
                    "categorization.science_domain": "computer_science",
                    "contact.person.given_name": "Katherine",
                    "contact.person.family_name": "Johnson",
                    "contact.person.email": "kj@example.org",
                    "sponsor_organizations": [{"name": "DOE", "ror_id": "not_applicable"}],
                    "research_organizations": [{"name": "LANL", "ror_id": "not_applicable"}],
                    "provenance.was_generated_by": "Automated feature extraction workflow",
                    "license.spdx_id": "Apache-2.0",
                    "license.name": "Apache License 2.0",
                    "dates.data_collection_start": "2024-02-01",
                    "dates.data_collection_end": "2024-02-02",
                    "stewardship.level": "project_managed",
                    "stewardship.update_frequency": "ad_hoc",
                    "ai_usage.ai_ready": "conditional",
                    "ai_usage.training_use_allowed": "true",
                    "ai_usage.inference_use_allowed": "conditional",
                    "ai_usage.evaluation_use_allowed": "true",
                    "ai_usage.human_review_required": True,
                    "data_quality.completeness": "All rows present.",
                    "data_quality.known_issues": "No major issues.",
                    "data_quality.validation_methods": "Validated against baseline run.",
                    "semantic_layer.schema_url": "https://example.org/schema.json",
                    "semantic_layer.semantic_context": ["Custom ML schema"],
                },
            )
            result = self.run_cli(
                "run",
                str(FIXTURES / "ai_ready_dataset"),
                "--profile",
                "ai_ready",
                "--output-root",
                str(output_root),
                "--answers",
                str(answers),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            checksum_manifest = output_root / "ai_ready_dataset" / "automation_output" / "checksums.sha256"
            self.assertTrue(checksum_manifest.exists())
            card = next(output_root.glob("ai_ready_dataset/validation_output/*.md"))
            text = card.read_text(encoding="utf-8")
            self.assertIn("Representative fields include", text)
            self.assertIn("Schema URL: https://example.org/schema.json", text)

    def test_sensitive_pipeline_enforces_sensitive_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "runs"
            answers = Path(tmpdir) / "answers.yaml"
            write_answers(
                answers,
                {
                    "identification.project": "genesis-sensitive",
                    "categorization.science_domain": "physics",
                    "contact.person.given_name": "Marie",
                    "contact.person.family_name": "Curie",
                    "contact.person.email": "marie@example.org",
                    "sponsor_organizations": [{"name": "NNSA", "ror_id": "not_applicable"}],
                    "research_organizations": [{"name": "Sandia National Laboratories", "ror_id": "not_applicable"}],
                    "provenance.was_generated_by": "Restricted instrument acquisition",
                    "license.spdx_id": "BSD-3-Clause",
                    "license.name": "BSD 3-Clause License",
                    "dates.data_collection_start": "2024-03-01",
                    "dates.data_collection_end": "2024-03-15",
                    "security.classification": "CUI",
                    "security.export_control": "EAR",
                    "security.export_control_id": "EAR99",
                    "security.classification_reason": "Contains export controlled parameters",
                    "security.declassification.review_date": "2024-03-20",
                    "security.declassification.authority": "Office of Classification",
                    "stewardship.level": "project_managed",
                    "stewardship.update_frequency": "annually",
                    "compliance.export_control_reviewed": True,
                    "compliance.irb_approved": "not_applicable",
                    "compliance.security_review_completed": True,
                },
            )
            result = self.run_cli(
                "run",
                str(FIXTURES / "sensitive_dataset"),
                "--profile",
                "sensitive",
                "--output-root",
                str(output_root),
                "--answers",
                str(answers),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = output_root / "sensitive_dataset" / "validation_output" / "validation_report.json"
            self.assertIn('"ok": true', report.read_text(encoding="utf-8"))

    def test_noninteractive_run_reports_unresolved_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "runs"
            answers = Path(tmpdir) / "answers.yaml"
            write_answers(answers, {})
            result = self.run_cli(
                "run",
                str(FIXTURES / "core_dataset"),
                "--profile",
                "core",
                "--output-root",
                str(output_root),
                "--answers",
                str(answers),
            )
            self.assertEqual(result.returncode, 1)
            unresolved = output_root / "core_dataset" / "automation_output" / "unresolved_fields.json"
            self.assertTrue(unresolved.exists())


if __name__ == "__main__":
    unittest.main()
