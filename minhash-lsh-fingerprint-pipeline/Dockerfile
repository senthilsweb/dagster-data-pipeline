# ─── Stage 1: build ───────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# System deps for python-magic and pip wheel builds
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libmagic1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --upgrade pip --quiet \
    && pip install --no-cache-dir --prefix=/install . \
    && pip install --no-cache-dir --prefix=/install "dagster-webserver>=1.9"


# ─── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Install Java 21 (required by Apache Tika) and libmagic
RUN apt-get update && apt-get install -y --no-install-recommends \
        openjdk-21-jre-headless \
        libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy pipeline source so relative imports & workspace.yaml resolution work
COPY . /app/minhash-lsh-fingerprint-pipeline/

# Copy root-level dagster config (workspace.yaml, dagster.yaml live one level up
# in the mono-repo; we inline a minimal Dagster config for the container here)
COPY dagster-container.yaml /dagster_home/dagster.yaml

ENV DAGSTER_HOME=/dagster_home \
    DOCFP_OUTPUT_ROOT=/data/output \
    PYTHONUNBUFFERED=1

VOLUME ["/data/input", "/data/output", "/dagster_home"]

EXPOSE 3000

CMD ["dagster", "dev", \
     "-w", "/app/minhash-lsh-fingerprint-pipeline/workspace.yaml", \
     "--host", "0.0.0.0", \
     "--port", "3000"]
