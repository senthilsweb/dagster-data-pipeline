## Why

The MinHash document-similarity pipeline needs a realistic mixed corpus of `.docx`, `.pdf`, and `.md` files to test fingerprinting and near-duplicate detection end-to-end. The raw `articles_100.train` data exists but only as a flat text file; it cannot be fed directly into a production document-ingestion pipeline that consumes office and portable-document formats.

## What Changes

- A Python one-time script (`generate_docs.py`) reads the 100-row training file and emits exactly one output document per row.
- File type is assigned by cycling `.docx → .pdf → .md` across the 100 rows (~34 / 33 / 33 distribution).
- Each filename is derived from the three most distinctive non-stopword content words plus the source doc-id (e.g., `man_shot_dead_t980.docx`), guaranteeing semantic uniqueness.
- A dedicated virtual environment (`.venv`) is created inside `minhash-doc-similarity/` with `python-docx`, `reportlab`, and `structlog`.
- OpenSpec is initialised for the project with support for both **Claude Code** and **GitHub Copilot**.

## Capabilities

### New Capabilities

- `synthetic-corpus-generation`: One-time script that converts a flat `.train` file into a mixed-format document corpus suitable for downstream MinHash pipeline ingestion.

### Modified Capabilities

<!-- none -->

## Impact

- **New files**: `generate_docs.py`, `.venv/`, `data/input/` (100 generated documents)
- **Dependencies added**: `python-docx 1.2.0`, `reportlab 4.5.0`, `structlog`, `pillow`, `lxml`
- **OpenSpec scaffolding**: `openspec/`, `.claude/`, `.github/` added to project root
- **No breaking changes** to existing MinHash or dagster-data-pipeline code
