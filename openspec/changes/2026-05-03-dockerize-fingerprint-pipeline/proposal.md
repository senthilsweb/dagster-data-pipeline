## Why

The document fingerprinting pipeline currently requires a local Python 3.12 venv, a Homebrew `libmagic`
install, and a Java runtime for Apache Tika. Onboarding contributors, running the pipeline in CI, or
deploying it to a server all depend on replicating this environment manually. A Docker-based setup
eliminates environment drift, encapsulates all system dependencies, and makes the pipeline runnable
with a single `docker compose up`.

## What Changes

- Add a multi-stage **`Dockerfile`** to `document-fingerprint-pipeline/` that builds a self-contained
  image with Python 3.12, Java 17, `libmagic`, and the `docfp` package pre-installed.
- Add a **`docker-compose.yaml`** at the project root (`minhash-doc-similarity/`) that wires:
  - the Dagster webserver + daemon service
  - bind-mount volumes for `data/input/` and `data/output/`
  - all runtime configuration via `.env` / environment variables
- Add a **`sample.env`** alongside `docker-compose.yaml` documenting every configurable variable.
- The existing `workspace.yaml` and `dagster.yaml` remain unchanged; they are copied into the image.
- No changes to pipeline Python code.

## Capabilities

### New Capabilities

- `docker-image`: A reproducible OCI image (`docfp:latest`) that runs `dagster dev` without any host
  Python, Java, or system library prerequisites.
- `volume-mounts`: Input documents and all output artifacts (metadata, text, normalized, shingles,
  signatures, indexes) are persisted on the host via named bind mounts, surviving container restarts.
- `env-configuration`: All pipeline tunables (output root, Tika server URL, Dagster home, DLP mode,
  shingle size, MinHash perm count, LSH threshold, log level) are injectable as environment variables
  without rebuilding the image.
- `dagster-home-persistence`: `DAGSTER_HOME` is mounted as a volume so run history, logs, and the
  Dagster SQLite instance survive container restarts.

### Modified Capabilities

- `dagster-orchestration`: Dagster is now launched inside the container; `dagster dev` listens on
  `0.0.0.0:3000` and is exposed to the host via port mapping.

## Impact

- **New files**: `document-fingerprint-pipeline/Dockerfile`,
  `minhash-doc-similarity/docker-compose.yaml`, `minhash-doc-similarity/sample.env`
- **No code changes** to `src/docfp/` or any existing pipeline file
- **Java 17 + libmagic** are bundled in the image — no host prerequisites beyond Docker
- **Image size estimate**: ~900 MB (Python 3.12 slim + Java 17 headless + Tika JAR ~60 MB)
- **Data volumes**: `data/input/` and `data/output/` are bind-mounted read-write; the host path is
  configurable via `INPUT_DIR` and `OUTPUT_DIR` env vars
