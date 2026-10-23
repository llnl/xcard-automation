from pathlib import Path

import pytest


@pytest.fixture
def dataset_dir(tmp_path: Path) -> Path:
    """Create a small representative dataset directory."""
    dataset = tmp_path / "sample_dataset"
    dataset.mkdir()
    (dataset / "README.md").write_text(
        "# Sample Materials Dataset\n\nA materials dataset for testing.",
        encoding="utf-8",
    )
    (dataset / "records.csv").write_text(
        "sample,value\nA,1\nB,2\n",
        encoding="utf-8",
    )
    (dataset / "LICENSE").write_text("MIT License", encoding="utf-8")
    return dataset


@pytest.fixture
def complete_answers() -> dict[str, object]:
    """Return the answers required for a core-profile datacard."""
    return {
        "identification.project": "genesis",
        "categorization.science_domain": "materials_science",
        "contact.person.given_name": "Ada",
        "contact.person.family_name": "Lovelace",
        "contact.person.email": "ada@example.org",
        "sponsor_organizations": [{"name": "DOE", "ror_id": "not_applicable"}],
        "research_organizations": [
            {"name": "Example Laboratory", "ror_id": "not_applicable"}
        ],
        "provenance.was_generated_by": "A test acquisition workflow",
    }
