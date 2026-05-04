# Document Fingerprinting Pipeline

A Dagster-native pipeline for document fingerprinting using MinHash/LSH similarity detection.

## Structure

```
src/docfp/
├── models/         # Dataclasses: DocumentMetadata, ExtractedDocumentText,
│                   #   NormalizedText, ShingleRecord
├── interfaces/     # ABCs — swap extractors/normalizers/hashers without changing pipeline
├── extractors/     # TikaDocumentTextExtractor (default); Docling + MarkItDown stubs
├── processors/     # Normalization, shingling, hashing, MinHash, LSH, DLP retention
├── writers/        # Artifact writers (JSON, Parquet, plain text)
└── dagster_defs/   # Dagster assets, jobs, resources, schedules
```

## Quick Start

```bash
# From dagster-data-pipeline/ (mono-repo root)
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e "minhash-lsh-fingerprint-pipeline/[dev]"

# End-to-end smoke test against a single document
cd minhash-lsh-fingerprint-pipeline
python test_task7_e2e.py

# Launch Dagster UI — all pipelines in one view
cd ..  # back to dagster-data-pipeline/
dagster dev -w workspace.yaml
# then open http://127.0.0.1:3000

# Or run just this pipeline standalone
dagster dev -w minhash-lsh-fingerprint-pipeline/workspace.yaml
```

## Pipeline DAG (12 assets)

```
source_document
  └─ document_metadata_json       {doc}.metadata.json
       └─ raw_extracted_text      {doc}.extracted.txt
            └─ ocr_extracted_text (pass-through or OCR — Task 8)
                 └─ normalized_text          {doc}.normalized.txt
                      └─ document_shingles
                           └─ document_shingle_hashes
                                └─ document_shingle_parquet   {doc}_shingle.parquet
                                     └─ document_hash_signature
                                          └─ document_minhash_signature
                                               ├─ {doc}.hash_signature.json
                                               ├─ {doc}.minhash.json
                                               └─ lsh_index
                                                    └─ corpus_lsh_index.pkl
                                                         └─ document_fingerprint_summary
```

## Output Artifacts

| File | Description |
|------|-------------|
| `metadata/{doc}.metadata.json` | `document_id` (SHA-256 of file), MIME type, file size, pipeline run ID |
| `text/{doc}.extracted.txt` | Raw text from Tika (or plain-text fallback) |
| `normalized/{doc}.normalized.txt` | NFC → lowercase → no punctuation → collapsed whitespace |
| `shingles/{doc}_shingle.parquet` | 17-column Parquet: shingle text, sha256, xxhash64, token/char offsets. DLP-safe mode deletes this after signing. |
| `signatures/{doc}.hash_signature.json` | Full provenance record: `hash_signature_sha256` (exact-match fingerprint), `minhash_signature` (128 values for Jaccard), shingle counts, schema version |
| `signatures/{doc}.minhash.json` | Lean query token: just `hashvalues` + `num_perm` — load this to query the LSH index |
| `indexes/corpus_lsh_index.pkl` | Pickled `MinHashLSH(threshold=0.5, num_perm=128)` — grows as documents are processed |

### `hash_signature.json` vs `minhash.json`

- **`hash_signature.json`** — audit record. `hash_signature_sha256` is a deterministic exact-match fingerprint (same document = identical hash every run). Also embeds the MinHash values and full provenance.
- **`minhash.json`** — query token only. Contains the same 128 MinHash values but no provenance. Load it when querying the LSH index to find near-duplicate documents.

### Querying the LSH index

```python
from docfp.processors.lsh_index_builder import LshIndexBuilder
import json, numpy as np
from datasketch import MinHash

lsh = LshIndexBuilder().load("data/output/indexes/corpus_lsh_index.pkl")

# Load a document's minhash.json and reconstruct a MinHash object
with open("data/output/signatures/some_doc.minhash.json") as f:
    m = json.load(f)
mh = MinHash(num_perm=m["num_perm"])
mh.hashvalues = np.array(m["hashvalues"], dtype=np.uint32)

# Returns document_ids of all corpus docs with Jaccard ≥ 0.5
candidates = LshIndexBuilder().query(lsh, mh)
print(candidates)
```

## Pipeline Configuration (`PipelineConfig`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `source_uri` | — | Absolute path to input document |
| `output_root` | `"output"` | Root output directory |
| `shingle_size` | `5` | Word n-gram window size |
| `minhash_num_perm` | `128` | MinHash permutation count |
| `lsh_threshold` | `0.5` | Jaccard similarity threshold |
| `dlp_safe_mode` | `True` | Delete shingle Parquet after signing |
| `ocr_enabled` | `False` | Force OCR regardless of extracted text |
| `ocr_min_text_length` | `50` | Trigger OCR when extracted text shorter than this |

## Text Extraction Engines

| Engine | Status | Notes |
|--------|--------|-------|
| `tika` | ✅ Default | Requires Java; auto-downloads server JAR |
| `docling` | 🔲 Stub | Raises `NotImplementedError` |
| `markitdown` | 🔲 Stub | Raises `NotImplementedError` |

Switch engine via `TextExtractorResource(engine="tika")` in `dagster_defs/resources.py`.

## Requirements

- Python 3.12+
- Java 8+ (for Tika)
- `libmagic` (`brew install libmagic` on macOS)
- See `pyproject.toml` for full dependency list

## Docker

```bash
# Pull from GitHub Container Registry
docker pull ghcr.io/senthilsweb/minlsh:latest

# Run standalone (no docker-compose)
docker run -p 3000:3000 \
  -v "$(pwd)/data/input:/data/input" \
  -v "$(pwd)/data/output:/data/output" \
  ghcr.io/senthilsweb/minlsh:latest

# Or use docker compose from the mono-repo root (dagster-data-pipeline/)
cp ../sample.env ../.env
docker compose -f ../docker-compose.yaml up -d
# → http://localhost:3000
```

> **Image:** `ghcr.io/senthilsweb/minlsh` — built for `linux/amd64` and `linux/arm64`  
> **CI/CD:** every git tag `v*` triggers a GitHub Actions build + push via `.github/workflows/minlsh-docker.yml`

