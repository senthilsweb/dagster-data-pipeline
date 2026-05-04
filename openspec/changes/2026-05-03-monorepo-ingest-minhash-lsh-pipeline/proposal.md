## Why

`minhash-doc-similarity` is a standalone repo that shares the same Dagster runtime, coding conventions,
OpenSpec change-management process, and developer tooling as `dagster-data-pipeline`. Keeping them
separate creates duplicated CI setup, separate venvs, split documentation, and no shared lineage view
in the Dagster UI. Merging them into a mono-repo:

- Gives a single `dagster dev` workspace that shows all pipelines in one Asset Catalog
- Eliminates duplicate `requirements.txt` / `pyproject.toml` management
- Consolidates OpenSpec change history under one repo
- Makes Docker packaging (already proposed in `2026-05-03-dockerize-fingerprint-pipeline`) simpler —
  one `docker-compose.yaml` covers every pipeline

## What Changes

- `minhash-doc-similarity/` is dissolved. Its contents are reorganised into `dagster-data-pipeline/`
  as follows:

  | Source | Destination |
  |--------|-------------|
  | `minhash-doc-similarity/document-fingerprint-pipeline/` | `dagster-data-pipeline/minhash-lsh-fingerprint-pipeline/` |
  | `minhash-doc-similarity/generate_docs.py` | `dagster-data-pipeline/minhash-lsh-fingerprint-pipeline/generate_docs.py` |
  | `minhash-doc-similarity/data/input/` | `dagster-data-pipeline/minhash-lsh-fingerprint-pipeline/data/input/` |
  | `minhash-doc-similarity/data/output/` | `dagster-data-pipeline/minhash-lsh-fingerprint-pipeline/data/output/` |
  | `minhash-doc-similarity/openspec/` | merged into `dagster-data-pipeline/openspec/` |
  | `minhash-doc-similarity/docker-compose.yaml` (from dockerize proposal) | `dagster-data-pipeline/docker-compose.yaml` |
  | `minhash-doc-similarity/sample.env` | `dagster-data-pipeline/sample.env` |

- The renamed sub-folder is **`minhash-lsh-fingerprint-pipeline/`** — it makes the scope
  (MinHash + LSH + fingerprinting) immediately visible, matches the mono-repo naming convention
  (`<domain>-pipeline`), and is shorter than `minhash-doc-similarity`.

- `dagster-data-pipeline/` gains a root `workspace.yaml` that loads both the legacy pipeline
  (`es-indexer`, `text-extract-from-pdf`) and `minhash-lsh-fingerprint-pipeline`.

- `minhash-doc-similarity/` is **deleted** after all tests pass on the mono-repo.

## Capabilities

### New Capabilities

- `monorepo-workspace`: Single `dagster dev` invocation shows all pipelines; unified Asset Catalog
  and run history.
- `openspec-in-dagster-data-pipeline`: OpenSpec is initialised at `dagster-data-pipeline/openspec/`
  with the existing pipeline as the first tracked change.

### Modified Capabilities

- `minhash-lsh-fingerprint-pipeline` (renamed from `minhash-doc-similarity/document-fingerprint-pipeline`):
  path changes only, no code changes.
- `generate_docs.py` moves inside `minhash-lsh-fingerprint-pipeline/` — no code changes.

## Non-Goals

- Merging the Python packages into a single `pyproject.toml` — each pipeline keeps its own.
- Changing any pipeline logic, asset definitions, or processor code.
- Migrating the legacy `es-indexer.py` / `text-extract-from-pdf.py` to the `docfp` package structure.

## Impact

- **Repo**: `dagster-data-pipeline` gains new sub-folder, root `workspace.yaml`, root `docker-compose.yaml`, OpenSpec
- **Deleted**: entire `minhash-doc-similarity/` directory after validated move
- **Root README**: updated with mono-repo structure and links to each pipeline
- **CI**: any GitHub Actions in `minhash-doc-similarity/.github/` are migrated to `dagster-data-pipeline/.github/`
- **Git history**: preserved via `git mv` (not copy+delete)
