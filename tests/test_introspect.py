from pathlib import Path

from xcard_automation.core.introspect import build_checksum_manifest, inspect_dataset


def test_inspect_dataset_reads_common_metadata(dataset_dir: Path) -> None:
    result = inspect_dataset(dataset_dir)

    assert result["formats"] == ["CSV", "Markdown"]
    assert result["readme_title"] == "Sample Materials Dataset"
    assert result["sample_columns"] == {"records.csv": ["sample", "value"]}
    assert result["csv_row_counts"] == {"records.csv": 2}
    assert result["license_guess"] == "MIT"


def test_checksum_manifest_contains_each_dataset_file(dataset_dir: Path, tmp_path: Path) -> None:
    manifest = build_checksum_manifest(dataset_dir, tmp_path / "checksums.sha256")

    assert manifest["type"] == "sha256"
    assert len(manifest["value"]) == 64
    assert "records.csv" in (tmp_path / "checksums.sha256").read_text(encoding="utf-8")
