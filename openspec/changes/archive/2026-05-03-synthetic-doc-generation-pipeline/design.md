## Approach

Generate synthetic document files from a flat news-article training corpus using a pure-Python one-time script. Each training row produces exactly one output file; format is distributed evenly by cycling docx → pdf → md. Filenames are derived from article content for semantic clarity.

## Architecture

```
articles_100.train  →  generate_docs.py  →  data/input/  (100 files)
     (flat text)           (one-time)         .docx / .pdf / .md
```

The script is intentionally stateless and idempotent — re-running overwrites outputs cleanly. No pipeline orchestration is needed for a one-time generation task.

## Key Components

### `generate_docs.py`

| Function | Responsibility |
|---|---|
| `load_training_rows(file_path)` | Parse `<doc_id> <text>` lines from the `.train` file |
| `extract_title(text)` | Derive a display title from the first sentence (≤ 80 chars) |
| `build_content_slug(doc_id, text, seen_slugs)` | Produce a unique content-derived filename slug from the first 3 meaningful words + doc_id |
| `write_docx(path, title, body)` | Emit a `.docx` via `python-docx` with H1 heading + wrapped paragraphs |
| `write_pdf(path, title, body)` | Emit a `.pdf` via `reportlab` with Title + BodyText styles |
| `write_md(path, title, body)` | Emit a `.md` with `# title` heading + raw body |
| `generate_document(idx, doc_id, text, seen_slugs)` | Orchestrate format selection (cycle by row index) and dispatch to correct writer |
| `main()` | Entry point — load rows, iterate, log summary |

### File Type Distribution

```
Row index mod 3 == 0  →  .docx   (rows 1, 4, 7, …  → ~34 files)
Row index mod 3 == 1  →  .pdf    (rows 2, 5, 8, …  → ~33 files)
Row index mod 3 == 2  →  .md     (rows 3, 6, 9, …  → ~33 files)
```

### Slug Generation

```python
keywords = first 3 non-stopword alphabetic words (≥3 chars) from text
slug     = "{kw1}_{kw2}_{kw3}_{doc_id}"
# e.g.  man_shot_dead_t980
```

A shared `seen_slugs: set[str]` prevents collisions by appending `_2`, `_3`, etc. when identical slugs are produced.

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `python-docx` | 1.2.0 | `.docx` generation |
| `reportlab` | 4.5.0 | `.pdf` generation |
| `structlog` | latest | Structured JSON logging |
| `pillow` | 12.2.0 | ReportLab image support (transitive) |
| `lxml` | 6.1.0 | python-docx XML support (transitive) |

Virtual environment at `minhash-doc-similarity/.venv` (Python 3.12).

## Logging

Follows the `text-extract-from-pdf.py` convention:
- `structlog` configured with `JSONRenderer` + ISO timestamps
- Log file named `generate_docs_<YYYYMMDD_HHMMSS>.log` in the script directory
- One log entry per file written; summary entry on completion

## Coding Conventions

Follows the pattern established in `dagster-data-pipeline/text-extract-from-pdf.py`:
- Module-level docstring with File Name / Author / Date / Description / Note / Requirements
- `structlog` structured logging (same processor chain)
- Every function documented with Args: / Returns: docstrings
- Constants uppercase at module level; no magic strings inline
