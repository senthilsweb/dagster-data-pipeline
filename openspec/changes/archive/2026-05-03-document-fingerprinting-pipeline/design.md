## Approach

A Dagster-native asset pipeline where every processing stage is a separate, independently materializable
asset. The pipeline is interface-first — extraction, OCR, normalization, and hashing are all hidden behind
Python ABCs so implementations can be swapped without touching pipeline logic. Shingles are an
intermediate artifact; only signatures and indexes are long-lived.

---

## Architecture

```
Input Folder / URI
      │
      ▼
[1] DocumentDiscoveryProcessor       pathlib, Dagster config
      │
      ▼
[2] DocumentMetadataExtractor        os, pathlib, python-magic
      │
      ▼
[3] DocumentChecksumProcessor        hashlib (SHA-256 → document_id)
      │
      ▼
[4] MetadataJsonWriter               json → {doc}.metadata.json
      │
      ▼
[5] DocumentTextExtractor (ABC)
    ├── TikaDocumentTextExtractor    Apache Tika (POC default)
    ├── DoclingDocumentTextExtractor Docling (future)
    └── MarkItDownDocumentTextExtractor MarkItDown (future)
      │
      ▼
[6] OcrDecisionProcessor             custom logic (length threshold / config flag)
      │ (if OCR needed)
      ▼
[7] OcrProcessor                     OCRmyPDF / Tesseract
      │
      ▼
[8] RawTextWriter                    → {doc}.extracted.txt
      │
      ▼
[9] TextNormalizer                   re, unicodedata, optional NLTK
      │
      ▼
[10] NormalizedTextWriter            → {doc}.normalized.txt
      │
      ▼
[11] TokenizerProcessor              custom regex / optional NLTK
      │
      ▼
[12] WordShingleGenerator            sliding window (default size=5)
      │
      ▼
[13] ShingleHashProcessor            hashlib (SHA-256) + xxhash (64-bit)
      │
      ▼
[14] ShingleFrameBuilder             Polars / Pandas
      │
      ▼
[15] ShingleParquetWriter            PyArrow → {doc}_shingle.parquet (TEMP)
      │
      ├──────────────────────────────┐
      ▼                              ▼
[16] MinHashSignatureBuilder    DocumentSignatureWriter
     datasketch                  json / PyArrow
      │                              │
      ▼                              ▼
[17] LshIndexBuilder           {doc}.hash_signature.json
     datasketch                 {doc}.minhash.json
      │
      ▼
[18] ShingleRetentionProcessor  delete _shingle.parquet (DLP-safe mode)
      │
      ▼
[19] DagsterAssetMaterializer   attach metadata: row_count, sig_path, doc_id, status
      │
      ▼
[20] SimilarityScorer           LSH candidates → Jaccard score
```

**Document partitioning** runs horizontally across steps 12–16:
`DocumentPartitionProcessor` splits → per-partition shingles/signatures → `PartitionSignatureMerger` merges sorted unique shingle hash sets and MinHash states into final document-level signature.

---

## Project Structure

```
document-fingerprint-pipeline/
├── README.md
├── pyproject.toml
├── dagster.yaml
├── workspace.yaml
└── src/
    └── docfp/
        ├── __init__.py
        ├── models/
        │   ├── document_metadata.py
        │   ├── extracted_text.py
        │   ├── normalized_text.py
        │   └── shingle_record.py
        ├── interfaces/
        │   ├── document_text_extractor.py   # ABC: extract(source_uri) → ExtractedDocumentText
        │   ├── ocr_processor.py
        │   ├── normalizer.py
        │   ├── shingle_generator.py
        │   ├── shingle_hasher.py
        │   └── artifact_writer.py
        ├── extractors/
        │   ├── tika_extractor.py
        │   ├── docling_extractor.py
        │   └── markitdown_extractor.py
        ├── processors/
        │   ├── metadata_extractor.py
        │   ├── checksum_processor.py
        │   ├── ocr_decision_processor.py
        │   ├── text_normalizer.py
        │   ├── tokenizer.py
        │   ├── word_shingle_generator.py
        │   ├── shingle_hash_processor.py
        │   ├── minhash_signature_builder.py
        │   ├── lsh_index_builder.py
        │   ├── document_partition_processor.py
        │   ├── partition_signature_merger.py
        │   └── shingle_retention_processor.py
        ├── writers/
        │   ├── metadata_json_writer.py
        │   ├── text_writer.py
        │   ├── shingle_parquet_writer.py
        │   └── document_signature_writer.py
        └── dagster_defs/
            ├── assets.py
            ├── jobs.py
            ├── resources.py
            └── schedules.py
```

---

## Output File Naming Convention

| Artifact | Pattern | Example |
|---|---|---|
| Metadata JSON | `{doc}.metadata.json` | `contract_v1.metadata.json` |
| Extracted text | `{doc}.extracted.txt` | `contract_v1.extracted.txt` |
| Normalized text | `{doc}.normalized.txt` | `contract_v1.normalized.txt` |
| Shingle Parquet (temp) | `{doc}_shingle.parquet` | `contract_v1_shingle.parquet` |
| Hash signature | `{doc}.hash_signature.json` | `contract_v1.hash_signature.json` |
| MinHash signature | `{doc}.minhash.json` | `contract_v1.minhash.json` |
| LSH index | `corpus_lsh_index.pkl` | `corpus_lsh_index.pkl` |

---

## Key Interfaces

```python
# interfaces/document_text_extractor.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass
class ExtractedDocumentText:
    document_id: str
    source_uri: str
    text: str
    metadata: dict[str, Any]
    pages: list[dict[str, Any]]
    extraction_engine: str
    ocr_applied: bool

class DocumentTextExtractor(ABC):
    @abstractmethod
    def extract(self, source_uri: str) -> ExtractedDocumentText:
        pass
```

---

## Dagster Asset Map

| Dagster Asset | Description |
|---|---|
| `source_document` | Input document representation |
| `document_metadata_json` | Metadata + checksum output |
| `raw_extracted_text` | Text extracted via extractor interface |
| `ocr_extracted_text` | OCR output when applied |
| `normalized_text` | Clean normalized text |
| `document_shingles` | Generated shingles |
| `document_shingle_hashes` | Shingle hashes (SHA-256 + xxhash64) |
| `document_shingle_parquet` | Temporary columnar shingle file |
| `document_hash_signature` | Retained document-level hash signature |
| `document_minhash_signature` | Retained MinHash signature |
| `lsh_index` | Retained LSH index for candidate lookup |
| `document_fingerprint_summary` | Summary JSON for downstream matching |

---

## Architecture Decision Records

| ADR | Decision | Status |
|---|---|---|
| ADR-001 | Use Dagster as orchestration framework | Accepted |
| ADR-002 | Use Apache Tika as default POC text extractor | Accepted for POC |
| ADR-003 | Use pluggable `DocumentTextExtractor` interface | Accepted |
| ADR-004 | Use deterministic normalization (no heavy NLP) | Accepted |
| ADR-005 | Use 5-word shingles as fingerprinting unit | Accepted |
| ADR-006 | Shingle Parquet is temporary; delete after signature generation | Accepted |
| ADR-007 | Store metadata as JSON sidecar per document | Accepted |
| ADR-008 | Generate both SHA-256 and fast 64-bit hashes per shingle | Accepted |
| ADR-009 | Defer vector embeddings from POC scope | Accepted |
| ADR-010 | Include MinHash and LSH indexing in POC scope | Accepted |
| ADR-011 | Support document partitioning and final merge | Accepted |
| ADR-012 | Retain signatures only; delete raw shingles in DLP-safe mode | Accepted |

---

## Python Package Stack

| Area | Library |
|---|---|
| Orchestration | `dagster` |
| Metadata extraction | `os`, `pathlib`, `hashlib`, `python-magic` |
| Default extraction | `apache-tika` |
| Future parser | `docling` |
| Future Markdown parser | `markitdown` |
| OCR | `ocrmypdf` / `tesseract` |
| Normalization | `re`, `unicodedata`, optional `nltk` |
| Hashing | `hashlib`, `xxhash` |
| Columnar output | `pyarrow` |
| DataFrame | `polars` or `pandas` |
| Similarity / signatures | `datasketch` |
