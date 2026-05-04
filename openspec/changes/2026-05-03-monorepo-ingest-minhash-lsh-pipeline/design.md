## Approach

Move files using `git mv` to preserve history. Keep each pipeline as an independent
Python package with its own `pyproject.toml` and `src/` layout. Wire a shared root
`workspace.yaml` that lists both code locations so a single `dagster dev` discovers
all pipelines.

---

## Mono-repo Layout (target state)

```
dagster-data-pipeline/                      ← git root
├── .github/                                ← CI workflows (migrated from minhash-doc-similarity)
├── openspec/                               ← OpenSpec (new — initialized in this change)
│   ├── config.yaml
│   ├── specs/
│   └── changes/
│       └── 2026-05-03-monorepo-ingest-minhash-lsh-pipeline/
├── workspace.yaml                          ← NEW: loads all pipelines
├── docker-compose.yaml                     ← NEW: from dockerize proposal
├── sample.env                              ← NEW: from dockerize proposal
├── dagster.yaml                            ← NEW: shared instance config
│
├── minhash-lsh-fingerprint-pipeline/       ← RENAMED from minhash-doc-similarity/document-fingerprint-pipeline
│   ├── Dockerfile                          ← from dockerize proposal
│   ├── workspace.yaml                      ← kept (used by standalone dev)
│   ├── dagster.yaml
│   ├── pyproject.toml
│   ├── generate_docs.py                    ← MOVED from minhash-doc-similarity/generate_docs.py
│   ├── data/
│   │   ├── input/
│   │   └── output/
│   ├── src/
│   │   └── docfp/
│   │       ├── models/
│   │       ├── interfaces/
│   │       ├── extractors/
│   │       ├── processors/
│   │       ├── writers/
│   │       └── dagster_defs/
│   └── tests/
│
├── es-indexer.py                           ← existing (unchanged)
├── text-extract-from-pdf.py               ← existing (unchanged)
├── requirements.txt                        ← existing (unchanged)
└── README.md                               ← UPDATED with mono-repo overview
```

---

## Root workspace.yaml

```yaml
# dagster-data-pipeline/workspace.yaml
load_from:
  - python_file:
      relative_path: es-indexer.py
      working_directory: .
  - python_package:
      package_name: docfp.dagster_defs
      working_directory: minhash-lsh-fingerprint-pipeline
```

> Note: Legacy scripts (`es-indexer.py`, `text-extract-from-pdf.py`) are loaded directly
> as python files; the `docfp` package is loaded from its sub-directory.

---

## Sub-folder Name Rationale

| Candidate | Verdict |
|-----------|---------|
| `minhash-doc-similarity` | ❌ Too generic, implies a library not a pipeline |
| `minhash-lsh-doc-similarity-pipeline` | ⚠️ Long, `doc-similarity` undersells the fingerprinting aspect |
| `minhash-lsh-fingerprint-pipeline` | ✅ Concise, domain-accurate, matches `<tech>-<purpose>-pipeline` pattern |
| `doc-fingerprint-pipeline` | ⚠️ Loses the MinHash/LSH tech signal |

**Chosen**: `minhash-lsh-fingerprint-pipeline`

---

## Migration Steps (git-safe)

```bash
# 1. Add dagster-data-pipeline as a remote in minhash-doc-similarity
#    (to preserve history with git subtree or git mv)

# 2. Inside dagster-data-pipeline working tree:
git mv ../minhash-doc-similarity/document-fingerprint-pipeline \
       minhash-lsh-fingerprint-pipeline

# 3. Move generate_docs.py into the pipeline folder
git mv ../minhash-doc-similarity/generate_docs.py \
       minhash-lsh-fingerprint-pipeline/generate_docs.py

# 4. Move data/ folder
git mv ../minhash-doc-similarity/data \
       minhash-lsh-fingerprint-pipeline/data

# 5. Merge openspec/changes from minhash-doc-similarity
cp -r ../minhash-doc-similarity/openspec/changes/* openspec/changes/

# 6. Create root workspace.yaml, docker-compose.yaml, dagster.yaml, sample.env

# 7. Install the moved package in the shared venv
pip install -e "minhash-lsh-fingerprint-pipeline/[dev]"

# 8. Smoke test (see Tasks)

# 9. Delete source repo
rm -rf ../minhash-doc-similarity
```

---

## ADRs

### ADR-M01 — Folder naming: `minhash-lsh-fingerprint-pipeline`

**Decision**: Rename `document-fingerprint-pipeline` to `minhash-lsh-fingerprint-pipeline`.
**Rationale**: Communicates both the technique (MinHash + LSH) and the purpose (fingerprinting)
at a glance, consistent with the mono-repo convention of `<tech>-<purpose>-pipeline`.

### ADR-M02 — Each pipeline keeps its own `pyproject.toml`

**Decision**: Do not merge all dependencies into a root `pyproject.toml`.
**Rationale**: Each pipeline has different runtimes and dependency lifecycles. Isolation avoids
dependency conflicts and lets each pipeline be released or containerised independently.

### ADR-M03 — Root `workspace.yaml` for unified Dagster UI

**Decision**: Add a root `workspace.yaml` that loads all code locations.
**Rationale**: A single `dagster dev` from the repo root provides the unified Asset Catalog
and lineage view across all pipelines without restructuring the packages.

### ADR-M04 — `generate_docs.py` lives inside `minhash-lsh-fingerprint-pipeline/`

**Decision**: Move the one-off data-generation script inside the pipeline folder.
**Rationale**: It is a pipeline-specific utility (generates the synthetic corpus used by that
pipeline's tests). It does not belong at the mono-repo root alongside unrelated scripts.
