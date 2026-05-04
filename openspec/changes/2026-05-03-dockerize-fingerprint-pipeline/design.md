## Approach

Add Docker packaging on top of the existing `docfp` package without modifying any pipeline code.
The image installs all system dependencies (Java 17, libmagic) and the Python package, then runs
`dagster dev`. Runtime tuning (paths, thresholds, log level) is driven entirely by environment
variables so the same image works in dev, CI, and production.

---

## Architecture

```
docker compose up
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│  docfp container                                        │
│                                                         │
│  Base: python:3.12-slim + openjdk-17-jre + libmagic     │
│                                                         │
│  COPY document-fingerprint-pipeline/ → /app/            │
│  RUN pip install -e /app/[dev]                          │
│                                                         │
│  ENTRYPOINT dagster dev                                 │
│    -w /app/workspace.yaml                               │
│    --host 0.0.0.0 --port 3000                           │
│                                                         │
│  Volumes                                                │
│    /data/input   ← host: $INPUT_DIR                     │
│    /data/output  ← host: $OUTPUT_DIR                    │
│    /dagster_home ← host: $DAGSTER_HOME_DIR              │
│                                                         │
│  Ports: 3000 → $DAGSTER_PORT (default 3000)             │
└─────────────────────────────────────────────────────────┘
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DAGSTER_PORT` | `3000` | Host port Dagster webserver binds to |
| `INPUT_DIR` | `./data/input` | Host path bind-mounted to `/data/input` |
| `OUTPUT_DIR` | `./data/output` | Host path bind-mounted to `/data/output` |
| `DAGSTER_HOME_DIR` | `./dagster_home` | Host path for Dagster run history / SQLite |
| `DOCFP_OUTPUT_ROOT` | `/data/output` | Passed to `PipelineConfig.output_root` |
| `DOCFP_SHINGLE_SIZE` | `5` | Word n-gram window size |
| `DOCFP_MINHASH_NUM_PERM` | `128` | MinHash permutation count |
| `DOCFP_LSH_THRESHOLD` | `0.5` | Jaccard similarity threshold |
| `DOCFP_DLP_SAFE_MODE` | `true` | Delete shingle Parquet after signing |
| `DOCFP_OCR_ENABLED` | `false` | Force OCR regardless of text length |
| `DOCFP_LOG_LEVEL` | `INFO` | structlog level |
| `TIKA_SERVER_JAR` | *(auto-download)* | Optional: pre-staged Tika server JAR path |
| `JAVA_OPTS` | `-Xmx512m` | JVM options for embedded Tika server |

---

## File Layout (after implementation)

```
minhash-doc-similarity/
├── docker-compose.yaml          ← new: orchestrates all services
├── sample.env                   ← new: template for .env
├── dagster_home/                ← created at runtime; gitignored
├── data/
│   ├── input/                   ← bind-mounted read-write into container
│   └── output/                  ← bind-mounted read-write into container
└── document-fingerprint-pipeline/
    ├── Dockerfile               ← new: multi-stage image build
    ├── workspace.yaml           ← unchanged
    ├── dagster.yaml             ← unchanged
    └── src/docfp/               ← unchanged
```

---

## ADRs

### ADR-013 — Base image: python:3.12-slim + openjdk-17-jre-headless

**Decision**: Use `python:3.12-slim` as base and layer Java 17 headless on top via `apt-get`.
**Rationale**: Slim base keeps image small; headless JRE is sufficient for Tika server. Using a
single-stage build avoids complexity for a dev/POC image.
**Rejected**: Full `openjdk` images are significantly larger; `graalvm` is overkill.

### ADR-014 — Tika JAR pre-staged inside image

**Decision**: Download the Tika server JAR during `docker build` via `curl` and place it at
`/opt/tika/tika-server.jar`. Set `TIKA_SERVER_JAR=/opt/tika/tika-server.jar` in the image.
**Rationale**: Eliminates the 60 MB download at container startup; makes cold-start deterministic.
The JAR version is pinned in the `Dockerfile` ARG.
**Rejected**: Runtime download is unreliable in air-gapped environments.

### ADR-015 — `DAGSTER_HOME` as a named volume

**Decision**: Mount a host directory as `DAGSTER_HOME` rather than using an ephemeral volume.
**Rationale**: Preserves run history, event logs, and the Dagster SQLite database across `docker
compose down` / `up` cycles. The host path is user-configurable via `DAGSTER_HOME_DIR`.

### ADR-016 — No separate daemon container for POC

**Decision**: Run both webserver and daemon in a single container via `dagster dev`.
**Rationale**: `dagster dev` bundles the webserver + asset daemon + scheduler daemon in one process,
which is appropriate for a POC/single-node deployment. A multi-service split (separate
`dagster-webserver` and `dagster-daemon` containers) can be added in a follow-up change.
