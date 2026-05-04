## Tasks

### 1. Environment setup
- [x] 1.1 Create virtual environment at `minhash-doc-similarity/.venv` using Python 3.12
- [x] 1.2 Install `python-docx`, `reportlab`, `structlog` into `.venv`

### 2. Script implementation
- [x] 2.1 Create `generate_docs.py` with module-level docstring (File Name / Author / Date / Description / Note / Requirements)
- [x] 2.2 Implement `load_training_rows()` — parse `<doc_id> <text>` lines
- [x] 2.3 Implement `extract_title()` — first sentence truncated to 80 chars
- [x] 2.4 Implement `build_content_slug()` — 3 distinctive keywords + doc_id, deduplication via `seen_slugs`
- [x] 2.5 Implement `write_docx()` — H1 heading + wrapped paragraphs via python-docx
- [x] 2.6 Implement `write_pdf()` — Title + BodyText paragraphs via reportlab
- [x] 2.7 Implement `write_md()` — `# heading` + plain body
- [x] 2.8 Implement `generate_document()` — format cycling (row index mod 3), dispatch to writer
- [x] 2.9 Implement `main()` — entry point, load rows, iterate, log summary
- [x] 2.10 Configure `structlog` with JSONRenderer + ISO timestamps + timestamped log file

### 3. Execution
- [x] 3.1 Run script: `.venv/bin/python generate_docs.py`
- [x] 3.2 Verify 100 files written to `data/input/` (34 `.docx`, 33 `.pdf`, 33 `.md`)
- [x] 3.3 Confirm all filenames are content-derived and unique

### 4. OpenSpec initialisation
- [x] 4.1 Install OpenSpec CLI globally: `npm install -g @fission-ai/openspec@latest`
- [x] 4.2 Run `openspec init` in `minhash-doc-similarity/` — select Claude Code + GitHub Copilot
- [x] 4.3 Verify `.claude/`, `.github/`, `openspec/` scaffolding created

### 5. Spec & archive
- [x] 5.1 Create OpenSpec change `synthetic-doc-generation-pipeline`
- [x] 5.2 Write `proposal.md`
- [x] 5.3 Write `design.md`
- [x] 5.4 Write `specs/synthetic-corpus-generation/spec.md`
- [x] 5.5 Write `tasks.md` (this file)
- [x] 5.6 Archive change
