# Canonical Data Card Template

This directory contains the **canonical data card template** used across projects.

## Purpose

- Provide a single, authoritative template for data cards.
- Ensure consistency and traceability across data stewardship efforts.
- Support automated tooling for validation and integration.

## Versioned Templates

The **canonical** template is the merged Genesis markdown datacard at `template.md`.

Legacy template generations previously stored in this directory now live under `archive/templates/data-card/`.

The semantic version recorded in the root `VERSION` file is the governed release version for the repository's canonical template lineage. The current release is `0.2.0`.

## Contents

- `template.md` - The canonical merged markdown datacard template.
- `README.md` - Guidance for how the canonical template is managed in this repository.

Supporting historical assets and prior generations live under `archive/templates/data-card/`.

## Governance

Changes to the canonical template:

- Must be proposed via merge requests.
- Must be reviewed and approved by template maintainers defined in `CODEOWNERS`.
- Must update:
  - The root `VERSION` file (semantic versioning).
  - `CHANGELOG.md` with a description of changes.
  - `governance/compatibility-matrix.md` if tool compatibility changes.

See:

- `governance/review-process.md`
- `governance/release-policy.md`
