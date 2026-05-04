## Why

Organizations need to detect whether sensitive documents — contracts, templates, reports, architecture
documents — have been copied, modified, reused, or partially leaked. Current approaches are either
manual and unscalable, checksum-only, full-text-search-based, or tightly coupled to a single parser.
A deterministic, explainable, and reusable document fingerprinting pipeline is needed that works across
all common enterprise document formats without relying on vector embeddings.

## What Changes

- Build a new **Dagster-orchestrated document fingerprinting pipeline** in `document-fingerprint-pipeline/`.
- Each pipeline step follows the **Single Responsibility Principle** and is independently materializable and rerunnable.
- A **pluggable `DocumentTextExtractor` interface** decouples extraction from pipeline logic; Apache Tika is the default POC extractor.
- **Word shingles (default size = 5)** are generated from normalized text, hashed with SHA-256 and xxhash64, and stored as **temporary Parquet** during processing only.
- **Document-level hash signatures**, **MinHash signatures**, and an **LSH index** are retained as permanent artifacts.
- Raw shingle Parquet is **deleted or expired** after signatures are generated in DLP-safe mode.
- **Document partitioning and partition-level merge** are supported for distributed execution.
- Output follows a strict **file naming convention** with metadata JSON sidecars.

## Capabilities

### New Capabilities

- `document-ingestion`: Accept and discover input documents from a configured folder/URI; extract file metadata and SHA-256 checksum.
- `text-extraction`: Extract text from supported formats (PDF, DOCX, DOC, PPTX, PPT, TXT, HTML, XLS/XLSX) through a pluggable interface; Apache Tika as default POC extractor.
- `ocr-processing`: Detect when OCR is required (extraction failure or explicit flag) and apply OCRmyPDF/Tesseract.
- `text-normalization`: Deterministic text normalization — lowercase, Unicode normalization, whitespace/punctuation cleanup, optional stopword removal.
- `shingle-generation`: Word-level shingle generation (default 5-word sliding window), shingle hashing (SHA-256 + xxhash64), temporary Parquet output.
- `document-signature`: Generate and retain document-level hash signatures; delete/expire raw shingle text after signature generation in DLP-safe mode.
- `minhash-lsh`: Generate MinHash signatures and build/persist an LSH index for approximate Jaccard similarity candidate lookup.
- `document-partitioning`: Split large documents into partitions for distributed processing; merge partition-level signatures into a final document-level signature.
- `dagster-orchestration`: Dagster asset/op definitions, step-level materialization metadata, rerun support, observability logging.

### Modified Capabilities

<!-- none — this is a greenfield pipeline -->

## Impact

- **New project root**: `document-fingerprint-pipeline/` with `src/docfp/` package layout
- **Dependencies**: Dagster, Apache Tika (Java/server), python-magic, hashlib, xxhash, PyArrow, Polars/Pandas, datasketch, OCRmyPDF/Tesseract, re/unicodedata
- **Output artifacts**: `.metadata.json`, `.extracted.txt`, `.normalized.txt`, `_shingle.parquet` (temporary), `.hash_signature.json`, `.minhash.json`, `corpus_lsh_index.pkl`
- **No changes** to existing dagster-data-pipeline or minhash-doc-similarity code
- **ADRs**: ADR-001 through ADR-012 documented in design.md
