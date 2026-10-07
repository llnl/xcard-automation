from __future__ import annotations

import csv
import hashlib
import json
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
from typing import Any

from .utils import sanitize_text

EXT_TO_FORMAT: dict[str, str] = {
    "csv": "CSV",
    "tsv": "TSV",
    "json": "JSON",
    "yaml": "YAML",
    "yml": "YAML",
    "h5": "HDF5",
    "hdf5": "HDF5",
    "nc": "NetCDF4",
    "nc4": "NetCDF4",
    "parquet": "Parquet",
    "arrow": "Arrow",
    "tif": "TIFF",
    "tiff": "TIFF",
    "png": "PNG",
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "txt": "Text",
    "md": "Markdown",
    "npy": "NumPy",
    "npz": "NumPy",
    "pt": "PyTorch",
    "pth": "PyTorch",
}


def inspect_dataset(dataset_dir: Path) -> dict[str, Any]:
    base = dataset_dir.resolve()
    all_files = [path for path in base.rglob("*") if path.is_file()]
    formats = sorted(
        {
            EXT_TO_FORMAT[path.suffix.lstrip(".").lower()]
            for path in all_files
            if path.suffix.lstrip(".").lower() in EXT_TO_FORMAT
        }
    )

    total_bytes = 0
    for path in all_files:
        try:
            total_bytes += path.stat().st_size
        except OSError:
            continue

    readme_path = _find_first(base, ("README",), max_depth=2)
    citation_path = _find_first(base, ("CITATION",), max_depth=2)
    license_path = _find_first(base, ("LICENSE", "COPYING"), max_depth=2)
    sample_columns = {}
    csv_rows = {}
    for csv_path in [path for path in all_files if path.suffix.lower() == ".csv"][:3]:
        columns, row_count = _sample_csv(csv_path)
        if columns:
            sample_columns[csv_path.name] = columns
            csv_rows[csv_path.name] = row_count

    readme_text = readme_path.read_text(encoding="utf-8", errors="replace") if readme_path else ""
    readme_title = _readme_title(readme_text)
    readme_summary = _readme_summary(readme_text)
    readme_keywords = _readme_keywords(readme_text)
    citation_info = _parse_citation(citation_path) if citation_path else {}
    license_hint = _license_hint(license_path) if license_path else ""

    return {
        "path": str(base),
        "dataset_slug": base.name,
        "file_count": len(all_files),
        "total_bytes": total_bytes,
        "formats": formats,
        "sample_columns": sample_columns,
        "csv_row_counts": csv_rows,
        "splits_detected": _detect_splits(base),
        "readme_file": str(readme_path) if readme_path else "",
        "readme_title": readme_title,
        "readme_summary": readme_summary,
        "readme_keywords": readme_keywords,
        "citation_file": str(citation_path) if citation_path else "",
        "citation": citation_info,
        "license_file": str(license_path) if license_path else "",
        "license_hint": license_hint,
        "license_guess": _guess_spdx(license_hint),
    }


def build_checksum_manifest(dataset_dir: Path, output_path: Path) -> dict[str, Any]:
    lines: list[str] = []
    digest = hashlib.sha256()
    for path in sorted(p for p in dataset_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(dataset_dir).as_posix()
        file_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        line = f"{file_digest}  {rel}"
        lines.append(line)
        digest.update(line.encode("utf-8"))
        digest.update(b"\n")
    output_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return {"type": "sha256", "value": digest.hexdigest(), "manifest_path": str(output_path)}


def inspect_as_json(dataset_dir: Path) -> str:
    return json.dumps(inspect_dataset(dataset_dir), indent=2)


def _find_first(base: Path, prefixes: tuple[str, ...], max_depth: int) -> Path | None:
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        if len(path.relative_to(base).parts) > max_depth:
            continue
        if any(path.name.upper().startswith(prefix.upper()) for prefix in prefixes):
            return path
    return None


def _sample_csv(path: Path) -> tuple[list[str], int]:
    columns: list[str] = []
    row_count = 0
    try:
        with path.open(encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            for index, row in enumerate(reader):
                if index == 0:
                    columns = [column.strip() for column in row]
                    continue
                row_count += 1
    except (OSError, csv.Error):
        return [], 0
    return columns, row_count


def _detect_splits(base: Path) -> list[str]:
    found: list[str] = []
    targets = {"train", "test", "val", "validation"}
    for path in base.rglob("*"):
        if not path.is_dir():
            continue
        if len(path.relative_to(base).parts) > 3:
            continue
        name = path.name.lower()
        if name in targets and name not in found:
            found.append(name)
    return found


def _readme_title(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return sanitize_text(stripped.lstrip("#"))
    return ""


def _readme_summary(text: str) -> str:
    chunks: list[str] = []
    for block in re.split(r"\n\s*\n", text):
        cleaned = sanitize_text(re.sub(r"^#+\s*", "", block))
        if cleaned:
            chunks.append(cleaned)
        if chunks:
            break
    return chunks[0] if chunks else ""


def _readme_keywords(text: str) -> list[str]:
    lowered = text.lower()
    found: list[str] = []
    for keyword in ["dataset", "simulation", "experiment", "materials", "image", "tabular", "timeseries", "sensor"]:
        if keyword in lowered and keyword not in found:
            found.append(keyword)
    return found


def _parse_citation(path: Path) -> dict[str, Any]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    title = ""
    version = ""
    doi = ""
    date_released = ""
    keywords: list[str] = []
    authors: list[dict[str, str]] = []
    current_author: dict[str, str] | None = None
    in_keywords = False
    in_authors = False
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw_line.startswith("title:"):
            title = raw_line.split(":", 1)[1].strip()
            in_keywords = False
            in_authors = False
        elif raw_line.startswith("version:"):
            version = raw_line.split(":", 1)[1].strip()
        elif raw_line.startswith("doi:"):
            doi = raw_line.split(":", 1)[1].strip()
        elif raw_line.startswith("date-released:"):
            date_released = raw_line.split(":", 1)[1].strip()
        elif raw_line.startswith("keywords:"):
            in_keywords = True
            in_authors = False
        elif raw_line.startswith("authors:"):
            in_authors = True
            in_keywords = False
        elif in_keywords and stripped.startswith("- "):
            keywords.append(stripped[2:].strip())
        elif in_authors and stripped.startswith("- "):
            if current_author:
                authors.append(current_author)
            current_author = {}
            payload = stripped[2:]
            if ":" in payload:
                key, value = payload.split(":", 1)
                current_author[key.strip()] = value.strip()
        elif in_authors and current_author is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current_author[key.strip()] = value.strip()
    if current_author:
        authors.append(current_author)
    normalized_authors = [
        {
            "given_name": author.get("given-names", ""),
            "family_name": author.get("family-names", ""),
            "orcid": author.get("orcid", "").replace("https://orcid.org/", ""),
            "affiliation_name": author.get("affiliation", ""),
            "email": author.get("email", ""),
        }
        for author in authors
    ]
    return {
        "title": title,
        "version": version,
        "doi": doi,
        "keywords": keywords,
        "date_released": date_released,
        "authors": normalized_authors,
    }


def _license_hint(path: Path) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[:5]
    except OSError:
        return ""
    return " ".join(sanitize_text(line) for line in lines if line.strip())[:200]


def _guess_spdx(text: str) -> str:
    lowered = text.lower()
    if "mit license" in lowered:
        return "MIT"
    if "apache license" in lowered:
        return "Apache-2.0"
    if "redistribution and use in source and binary forms" in lowered:
        return "BSD-3-Clause"
    if "creative commons attribution" in lowered:
        return "CC-BY-4.0"
    return ""
