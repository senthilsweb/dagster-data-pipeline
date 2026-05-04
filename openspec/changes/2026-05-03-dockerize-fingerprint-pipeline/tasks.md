## Tasks

### 1. Dockerfile
- [ ] 1.1 Write `document-fingerprint-pipeline/Dockerfile` — multi-stage:
  - Stage 1 `builder`: install build tools, `pip install -e /app/[dev]`
  - Stage 2 `runtime`: `python:3.12-slim`, copy venv from builder, install `openjdk-17-jre-headless` and `libmagic1` via `apt-get`
- [ ] 1.2 Pre-download Tika server JAR during build (`ARG TIKA_VERSION=3.1.0`); set `ENV TIKA_SERVER_JAR=/opt/tika/tika-server.jar`
- [ ] 1.3 Set `DAGSTER_HOME=/dagster_home`, `DOCFP_OUTPUT_ROOT=/data/output` as image defaults
- [ ] 1.4 `ENTRYPOINT ["dagster", "dev", "-w", "/app/workspace.yaml", "--host", "0.0.0.0", "--port", "3000"]`
- [ ] 1.5 Add `.dockerignore` to exclude `.venv/`, `__pycache__/`, `*.pyc`, `data/`, `dagster_home/`, test artefacts

### 2. docker-compose.yaml
- [ ] 2.1 Write `minhash-doc-similarity/docker-compose.yaml` with a single `docfp` service
- [ ] 2.2 Bind-mount `${INPUT_DIR:-./data/input}` → `/data/input` (read-write)
- [ ] 2.3 Bind-mount `${OUTPUT_DIR:-./data/output}` → `/data/output` (read-write)
- [ ] 2.4 Bind-mount `${DAGSTER_HOME_DIR:-./dagster_home}` → `/dagster_home` (read-write)
- [ ] 2.5 Port-map `${DAGSTER_PORT:-3000}:3000`
- [ ] 2.6 Forward all `DOCFP_*` and `TIKA_*` and `JAVA_OPTS` env vars from `.env` / host environment
- [ ] 2.7 Add `restart: unless-stopped` and a `healthcheck` hitting `http://localhost:3000/health`

### 3. sample.env
- [ ] 3.1 Write `minhash-doc-similarity/sample.env` with all variables from the design env table
- [ ] 3.2 Add comments explaining each variable and its effect on the pipeline
- [ ] 3.3 Add instructions at the top: `cp sample.env .env` before `docker compose up`

### 4. .gitignore / .dockerignore hygiene
- [ ] 4.1 Add `document-fingerprint-pipeline/.dockerignore`
- [ ] 4.2 Ensure `dagster_home/` and `data/output/` are in `.gitignore` at `minhash-doc-similarity/`

### 5. Smoke test
- [ ] 5.1 `docker build -t docfp:latest document-fingerprint-pipeline/` — verify clean build, no download errors
- [ ] 5.2 `docker compose up -d` — verify container starts and Dagster UI is reachable at `http://localhost:3000`
- [ ] 5.3 Verify all 12 assets appear in the Asset Catalog DAG view
- [ ] 5.4 Place one `.md` file in `data/input/`, trigger `fingerprint_pipeline_job` from the UI, confirm output artifacts appear in `data/output/`
- [ ] 5.5 `docker compose down && docker compose up -d` — verify run history is preserved (DAGSTER_HOME volume)
