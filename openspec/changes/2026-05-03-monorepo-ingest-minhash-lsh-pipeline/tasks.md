## Tasks

### 1. Initialize OpenSpec in dagster-data-pipeline
- [x] 1.1 Create `openspec/config.yaml` with project context and per-artifact rules
- [x] 1.2 Create `openspec/specs/` and `openspec/changes/` directories
- [x] 1.3 Create this change entry: `openspec/changes/2026-05-03-monorepo-ingest-minhash-lsh-pipeline/`

### 2. Move files into mono-repo
- [ ] 2.1 Copy `minhash-doc-similarity/document-fingerprint-pipeline/` → `minhash-lsh-fingerprint-pipeline/` (preserve contents)
- [ ] 2.2 Move `minhash-doc-similarity/generate_docs.py` → `minhash-lsh-fingerprint-pipeline/generate_docs.py`
- [ ] 2.3 Move `minhash-doc-similarity/data/` → `minhash-lsh-fingerprint-pipeline/data/`
- [ ] 2.4 Copy `minhash-doc-similarity/openspec/changes/*` → `dagster-data-pipeline/openspec/changes/`
- [ ] 2.5 Copy `minhash-doc-similarity/openspec/specs/*` → `dagster-data-pipeline/openspec/specs/`
- [ ] 2.6 Copy `minhash-doc-similarity/.github/` → `dagster-data-pipeline/.github/` (merge, do not overwrite existing workflows)

### 3. Create shared root config files
- [ ] 3.1 Write `dagster-data-pipeline/workspace.yaml` loading both legacy scripts and `docfp.dagster_defs`
- [ ] 3.2 Write `dagster-data-pipeline/dagster.yaml` (`telemetry: enabled: false`)
- [ ] 3.3 Write `dagster-data-pipeline/docker-compose.yaml` (from dockerize proposal, adapted for mono-repo path `minhash-lsh-fingerprint-pipeline/`)
- [ ] 3.4 Write `dagster-data-pipeline/sample.env` (all `DOCFP_*`, `TIKA_*`, `DAGSTER_*` variables)
- [ ] 3.5 Add `dagster_home/`, `minhash-lsh-fingerprint-pipeline/data/output/`, `*.log`, `.venv/` to `dagster-data-pipeline/.gitignore`

### 4. Update READMEs
- [ ] 4.1 Update `dagster-data-pipeline/README.md` — add mono-repo overview section with folder table, quick-start, and links to each pipeline README
- [ ] 4.2 Verify `minhash-lsh-fingerprint-pipeline/README.md` paths/references still correct after rename (update any hardcoded `minhash-doc-similarity` or `document-fingerprint-pipeline` paths)

### 5. Install and verify in the mono-repo venv
- [ ] 5.1 Create shared venv: `python3.12 -m venv .venv && source .venv/bin/activate`
- [ ] 5.2 Install pipeline package: `pip install -e "minhash-lsh-fingerprint-pipeline/[dev]"`
- [ ] 5.3 Verify import: `python -c "from docfp.dagster_defs import defs; print(len(list(defs.resolve_all_asset_keys())), 'assets')"`

### 6. Smoke tests in mono-repo
- [ ] 6.1 Run `python minhash-lsh-fingerprint-pipeline/test_task7.py` — expect "Task 7 PASS"
- [ ] 6.2 Run `python minhash-lsh-fingerprint-pipeline/test_task7_e2e.py` — expect "ALL STEPS PASSED"
- [ ] 6.3 Run `dagster dev -w workspace.yaml` — verify UI loads at `http://127.0.0.1:3000`
- [ ] 6.4 Confirm all 12 `docfp` assets visible in Asset Catalog
- [ ] 6.5 Place one `.md` file in `minhash-lsh-fingerprint-pipeline/data/input/`, trigger `fingerprint_pipeline_job` from UI, confirm artifacts in `data/output/`

### 7. Docker smoke test (from mono-repo root)
- [ ] 7.1 `docker build -t docfp:latest minhash-lsh-fingerprint-pipeline/` — clean build
- [ ] 7.2 `cp sample.env .env && docker compose up -d` — container starts
- [ ] 7.3 Verify `http://localhost:3000` reachable, 12 assets visible
- [ ] 7.4 `docker compose down` — clean shutdown

### 8. Delete source repo
- [ ] 8.1 Confirm all smoke tests above pass
- [ ] 8.2 `rm -rf /Users/krs/work/data-pipelines/minhash-doc-similarity` — delete original folder
- [ ] 8.3 Remove `minhash-doc-similarity` from VS Code workspace (`data-pipelines.code-workspace`)
- [ ] 8.4 Add `minhash-lsh-fingerprint-pipeline` to VS Code workspace file
