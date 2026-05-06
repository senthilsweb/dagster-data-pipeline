# Document Fingerprinting Pipeline using Dagster
## BRD and Architecture Decision Record — Updated Draft

*Generated: 2026-05-03 12:02 UTC*

---

## Document Purpose

This document defines the first draft Business Requirements Document (BRD) and Architecture Decision Record (ADR) for building a document fingerprinting pipeline that processes unstructured documents such as DOC, DOCX, PDF, PPT, PPTX, TXT, and other enterprise document formats.

The goal is to extract lightweight metadata, extract or OCR text, normalize content, create shingles, hash shingles, and store intermediate shingle artifacts in columnar Parquet only as needed during processing, then retain document-level hash signatures, MinHash signatures, and LSH index artifacts for downstream similarity matching and DLP-style document fingerprinting.

---

## 2. Business Objective

Organizations often need to detect whether sensitive documents, templates, reports, proposals, contracts, architecture documents, or internal documents are copied, modified, reused, or partially leaked.

This project will create a reusable pipeline that generates document-level hash signatures from temporary shingle records. These signatures will be used to identify near-duplicate documents, partial content reuse, similar templates, or document containment across a larger corpus without requiring long-term retention of raw shingle text.

---

## 3. Problem Statement

Current document comparison approaches are often either manual and not scalable, based on exact file checksum only, based on full-text search only, based on vector embeddings that may not be ideal for deterministic near-duplicate detection, or tightly coupled to one extraction tool or document parser.

A better approach is needed where each document is converted into deterministic, explainable, and reusable content fingerprints using shingling and hashing.

---

## 4. Proposed Solution

Build a Dagster-orchestrated document fingerprinting pipeline where each step follows the Single Responsibility Principle (SRP).

1. Extract basic metadata from the source file.
2. Calculate file checksum.
3. Extract text using a pluggable document extraction interface.
4. Apply OCR only when required or explicitly configured.
5. Normalize extracted text.
6. Generate word-level shingles.
7. Generate hash values for each shingle.
8. Store document metadata as JSON.
9. Store shingle records as temporary Parquet during processing only, unless debug retention is explicitly enabled.
10. Generate and persist document-level hash signatures.
11. Generate MinHash signatures as part of the POC scope.
12. Build and persist an LSH index as part of the POC scope.
13. Support document partitioning for distributed processing and final merge.

---

## 5. Scope

### 5.1 In Scope for POC

- Support common enterprise document formats: PDF, DOC, DOCX, PPT, PPTX, TXT, HTML, and XLS/XLSX if text extraction is required.
- Basic metadata extraction.
- SHA-256 checksum generation.
- Text extraction through a common interface.
- Optional OCR path based on configuration or extraction failure.
- Text normalization.
- Word shingle generation.
- Shingle hashing.
- Temporary Parquet file generation per document or document partition.
- Retention of document-level hash signatures after shingle processing.
- JSON metadata sidecar generation per document.
- MinHash signature generation.
- LSH index generation.
- Document partitioning support for distributed processing and final merge.
- Dagster-based orchestration.
- Step-level rerun capability.
- Basic logging and observability.

### 5.2 Out of Scope for POC

- Full semantic vector embedding search.
- Full DLP policy engine.
- UI for document upload.
- Advanced table extraction quality scoring.
- Advanced semantic classification.
- Entity extraction.
- Full document comparison UI.
- Access control and user-level governance.
- Production-grade scale tuning beyond partition-aware design.

---

## 6. Target Users

| User Type | Need |
|-----------|------|
| Data governance engineer | Detect reused or leaked sensitive documents |
| Data catalog engineer | Fingerprint documents during metadata harvesting |
| Security/DLP engineer | Identify near-duplicate sensitive documents |
| Search/indexing engineer | Prepare deterministic document signatures |
| QA/SDET/data pipeline engineer | Validate document processing pipelines |
| Enterprise architect | Build reusable document intelligence services |

---

## 7. High-Level Workflow

```
Input Document
  -> Metadata Extraction
  -> Checksum Calculation
  -> Text Extraction
  -> OCR Fallback / OCR Optional Path
  -> Text Normalization
  -> Shingle Generation
  -> Shingle Hashing
  -> Metadata JSON Output
  -> Temporary Shingle Parquet Output
  -> Document Hash Signature Output
  -> MinHash Signature Output
  -> LSH Index Build / Merge
```

---

## 8. Dagster Design Approach

The pipeline will be modeled using Dagster assets or ops. Each processing step should be independently materializable and rerunnable. This aligns with the existing Dagster data pipeline style, where every step performs one clear job and failed steps can be rerun without restarting the entire pipeline.

### 8.1 Suggested Dagster Assets

| Dagster Asset | Description |
|---------------|-------------|
| `source_document` | Represents the input document |
| `document_metadata_json` | Basic metadata and checksum output |
| `raw_extracted_text` | Text extracted from document |
| `ocr_extracted_text` | OCR output if OCR is applied |
| `normalized_text` | Clean normalized text |
| `document_shingles` | Generated shingles |
| `document_shingle_hashes` | Shingle hashes |
| `document_shingle_parquet` | Temporary columnar shingle file used during processing |
| `document_hash_signature` | Retained document-level hash signature artifact |
| `document_minhash_signature` | Retained MinHash signature artifact |
| `lsh_index` | Retained LSH index artifact for candidate lookup |
| `document_fingerprint_summary` | Summary JSON for downstream matching and audit |

---

## 9. Output File Naming Convention

### 9.1 Metadata JSON

```
{document_name_or_doc_fqdn}.metadata.json
Example: contract_template_v1.metadata.json
```

### 9.2 Extracted Text

```
{document_name_or_doc_fqdn}.extracted.txt
Example: contract_template_v1.extracted.txt
```

### 9.3 Normalized Text

```
{document_name_or_doc_fqdn}.normalized.txt
Example: contract_template_v1.normalized.txt
```

### 9.4 Shingle Parquet

```
{document_name_or_doc_fqdn}_shingle.parquet
Example: contract_template_v1_shingle.parquet
```

### 9.5 Retained Signature and Index Artifacts

```
{document_name_or_doc_fqdn}.hash_signature.json
{document_name_or_doc_fqdn}.minhash.json
corpus_lsh_index.pkl  or  corpus_lsh_index.parquet
```

The shingle Parquet file is considered an intermediate artifact. For DLP-sensitive workloads, the pipeline should delete or expire raw shingle text after document-level signatures are generated and validated.

---

## 10. Metadata JSON Structure

```json
{
    "document_id": "sha256:<file_checksum>",
    "source_uri": "/input/contracts/contract_template_v1.docx",
    "file_name": "contract_template_v1.docx",
    "file_extension": ".docx",
    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "size_bytes": 245678,
    "checksum_sha256": "<sha256>",
    "created_time_utc": null,
    "modified_time_utc": "2026-05-03T10:30:00Z",
    "pipeline_name": "document_fingerprinting_pipeline",
    "pipeline_version": "0.1.0",
    "metadata_extraction_engine": "python-stat-python-magic",
    "text_extraction_engine": "apache-tika",
    "ocr_applied": false,
    "normalization_version": "normalize-v1",
    "shingle_type": "word",
    "shingle_size": 5,
    "shingle_retention_policy": "delete_after_signature_generation",
    "partition_id": "part-00000",
    "partition_count": 1,
    "status": "completed"
}
```

---

## 11. Temporary Shingle Parquet Schema

The shingle Parquet artifact is useful for audit, debugging, partition-level processing, and final signature generation. However, because `shingle_text` may contain sensitive content, it should be treated as a temporary artifact and deleted or expired after signatures and index artifacts are generated, unless a controlled debug mode is enabled.

| Column Name | Type | Description |
|-------------|------|-------------|
| `document_id` | string | Stable document ID generated from file checksum |
| `partition_id` | string | Partition identifier for distributed processing |
| `partition_count` | int | Total partition count for the document |
| `source_uri` | string | Original document path or URI |
| `file_name` | string | Source file name |
| `page_no` | int | Page number if available |
| `section_id` | string | Optional section or heading ID |
| `shingle_id` | int | Sequential shingle number |
| `shingle_text` | string | Actual shingle text |
| `shingle_hash64` | string | Fast hash for indexing |
| `shingle_hash_sha256` | string | Stable cryptographic hash |
| `token_start` | int | Start token offset |
| `token_end` | int | End token offset |
| `char_start` | int | Start character offset if available |
| `char_end` | int | End character offset if available |
| `normalization_version` | string | Normalization version used |
| `created_at_utc` | timestamp | Pipeline processing timestamp |

### 11.1 Retained Document Signature Schema

| Column Name | Type | Description |
|-------------|------|-------------|
| `document_id` | string | Stable document ID generated from file checksum |
| `source_uri` | string | Original document path or URI |
| `file_name` | string | Source file name |
| `signature_version` | string | Signature generation version |
| `shingle_size` | int | Word shingle size used |
| `total_shingle_count` | long | Total shingles generated before retention cleanup |
| `unique_shingle_hash_count` | long | Unique shingle hashes used for similarity |
| `hash_signature_sha256` | string | Document-level digest derived from sorted unique shingle hashes |
| `minhash_signature` | array\<int/string\> | MinHash signature values generated for approximate Jaccard similarity |
| `lsh_bucket_keys` | array\<string\> | LSH bucket keys for candidate retrieval |
| `partition_merge_status` | string | Indicates single-partition or merged-partition signature status |
| `created_at_utc` | timestamp | Signature generation timestamp |

---

## 12. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-001 | The system shall accept document files from a configured input folder or URI. |
| FR-002 | The system shall extract basic file metadata without expensive profiling. |
| FR-003 | The system shall calculate SHA-256 checksum for each document. |
| FR-004 | The system shall detect file extension and MIME type. |
| FR-005 | The system shall extract text from supported document formats. |
| FR-006 | The system shall support a pluggable text extraction interface. |
| FR-007 | The system shall support Apache Tika as the default POC extractor. |
| FR-008 | The system shall allow Docling, MarkItDown, or custom extractors to be added later. |
| FR-009 | The system shall apply OCR when text extraction fails or when OCR is explicitly enabled. |
| FR-010 | The system shall normalize extracted text using deterministic rules. |
| FR-011 | The system shall generate word shingles from normalized text. |
| FR-012 | The system shall generate SHA-256 hash for each shingle. |
| FR-013 | The system shall generate fast 64-bit hash for each shingle. |
| FR-014 | The system shall write shingle records into temporary Parquet format for processing and audit. |
| FR-015 | The system shall write document metadata into JSON format. |
| FR-016 | The system shall support rerunning failed steps using Dagster. |
| FR-017 | The system shall log processing status and errors for every step. |
| FR-018 | The system shall support batch processing of multiple documents. |
| FR-019 | The system shall support document-level processing isolation. |
| FR-020 | The system shall avoid storing unnecessary profiling statistics in the POC. |
| FR-021 | The system shall generate and retain document-level hash signatures after shingle processing. |
| FR-022 | The system shall delete or expire raw shingle text artifacts after signature generation when DLP-safe mode is enabled. |
| FR-023 | The system shall generate MinHash signatures as part of the POC. |
| FR-024 | The system shall build and persist an LSH index as part of the POC. |
| FR-025 | The system shall support document partitioning for distributed processing. |
| FR-026 | The system shall merge partition-level signatures into a final document-level signature. |

---

## 13. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-001 | The design shall follow Single Responsibility Principle. |
| NFR-002 | Each processing step shall be independently testable. |
| NFR-003 | Each implementation shall be swappable behind an interface. |
| NFR-004 | The pipeline shall support local execution. |
| NFR-005 | The pipeline shall support future containerized execution. |
| NFR-006 | The pipeline shall avoid unnecessary NLP or embedding cost in POC. |
| NFR-007 | The output shall be columnar and suitable for large-scale analytics. |
| NFR-008 | The system shall be explainable and auditable. |
| NFR-009 | The system shall support MinHash and LSH indexing within the POC scope. |
| NFR-010 | The pipeline shall support observability using Dagster logs and materialization metadata. |

---

## 14. Recommended Python Package Stack for POC

| Area | Recommended Library |
|------|---------------------|
| Orchestration | Dagster |
| Metadata extraction | `os`, `pathlib`, `hashlib`, `python-magic` |
| Default document extraction | Apache Tika |
| Future parser option | Docling |
| Future Markdown-oriented parser | MarkItDown |
| OCR | OCRmyPDF / Tesseract |
| Normalization | Python `re`, `unicodedata`, optional NLTK stopwords |
| Shingling | Custom Python implementation |
| Hashing | `hashlib`, `xxhash` |
| Columnar output | PyArrow / Parquet |
| DataFrame processing | Polars or Pandas |
| Similarity and signatures | datasketch |
| Approximate matching | MinHash / LSH |
| Partition merge | Custom merge logic using sorted unique shingle hashes and datasketch-compatible MinHash merge |

---

## 15. Interface-Based Design

The POC should not directly bind the pipeline logic to a specific document extraction library. The Dagster asset should depend only on `DocumentTextExtractor`, not on Tika, Docling, or MarkItDown directly.

```python
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

class TikaDocumentTextExtractor(DocumentTextExtractor):
    def extract(self, source_uri: str) -> ExtractedDocumentText:
        pass

class DoclingDocumentTextExtractor(DocumentTextExtractor):
    def extract(self, source_uri: str) -> ExtractedDocumentText:
        pass

class MarkItDownDocumentTextExtractor(DocumentTextExtractor):
    def extract(self, source_uri: str) -> ExtractedDocumentText:
        pass
```

---

## 16. Architecture Decision Records (ADRs)

### ADR-001: Use Dagster as the Orchestration Framework

| Field | Decision |
|-------|----------|
| **Status** | Accepted |
| **Context** | The workflow has multiple independent processing steps such as metadata extraction, OCR, normalization, shingling, hashing, and Parquet generation. |
| **Decision** | Use Dagster to orchestrate the pipeline using assets or ops. |
| **Reason** | Dagster supports step-level materialization, observability, rerun of failed steps, and clean local development. |
| **Consequence** | Pipeline logic will be organized as Dagster assets/ops with clear dependencies. |

### ADR-002: Use Apache Tika as the Default POC Text Extraction Engine

| Field | Decision |
|-------|----------|
| **Status** | Accepted for POC |
| **Context** | The first POC requires broad support for old and new document formats such as DOC, DOCX, PDF, PPT, PPTX, XLS, XLSX, TXT, and HTML. |
| **Decision** | Use Apache Tika as the default text and metadata extraction engine for the POC. |
| **Reason** | Tika supports metadata and text extraction from 1000+ file types through a common interface. |
| **Consequence** | Java/Tika server dependency may be required. Future implementations can replace Tika behind the extractor interface. |

### ADR-003: Use Pluggable Extractor Interface

| Field | Decision |
|-------|----------|
| **Status** | Accepted |
| **Context** | Document parsing libraries vary in speed, quality, supported formats, and layout handling. |
| **Decision** | Create a `DocumentTextExtractor` interface and hide implementation-specific logic behind it. |
| **Reason** | This allows the POC to start with Tika and later switch to Docling, MarkItDown, PyMuPDF, or a Rust-based extractor. |
| **Consequence** | Slight upfront abstraction cost, but long-term maintainability improves. |

### ADR-004: Use Deterministic Normalization Instead of Heavy NLP

| Field | Decision |
|-------|----------|
| **Status** | Accepted |
| **Context** | The goal is document fingerprinting and near-duplicate detection, not semantic understanding. |
| **Decision** | Use lightweight deterministic normalization using lowercase, Unicode normalization, whitespace cleanup, punctuation handling, and optional stopword removal. |
| **Reason** | Deterministic text processing is easier to explain, reproduce, and debug. |
| **Consequence** | Advanced NLP features such as lemmatization and entity extraction are deferred. |

### ADR-005: Use Word Shingles as the Initial Fingerprinting Unit

| Field | Decision |
|-------|----------|
| **Status** | Accepted |
| **Context** | The system needs explainable document fingerprints suitable for similarity and containment detection. |
| **Decision** | Use word-level shingles as the default. Start with 5-word shingles. |
| **Reason** | Word shingles are easy to inspect, audit, and compare. They work well for near-duplicate document detection. |
| **Consequence** | Short text snippets may require smaller shingle sizes later. Character shingles may be added in future. |

### ADR-006: Use Shingle Parquet as a Temporary Processing Artifact

| Field | Decision |
|-------|----------|
| **Status** | Accepted |
| **Context** | Shingle output may become large and may contain sensitive fragments of the source document. |
| **Decision** | Store shingle records in Parquet during processing, but treat raw shingle text as temporary and delete or expire it after signature generation in DLP-safe mode. |
| **Reason** | Parquet is columnar, compact, analytics-friendly, and useful for partition-level processing and audit, but long-term retention of raw shingles may create DLP exposure. |
| **Consequence** | The retained artifact will be document-level hash signatures, MinHash signatures, and LSH index data, not raw shingle text. |

### ADR-007: Store Metadata as JSON Sidecar

| Field | Decision |
|-------|----------|
| **Status** | Accepted |
| **Context** | Metadata is document-level, semi-structured, and does not need to be repeated for every shingle row. |
| **Decision** | Store metadata as `{document_name_or_doc_fqdn}.metadata.json`. |
| **Reason** | JSON is easy to inspect, version, and pass between pipeline steps. |
| **Consequence** | Metadata and shingle outputs must be linked using `document_id`. |

### ADR-008: Generate Both SHA-256 and Fast 64-bit Hashes for Shingles

| Field | Decision |
|-------|----------|
| **Status** | Accepted |
| **Context** | Different downstream operations require different hash characteristics. |
| **Decision** | Generate SHA-256 and fast 64-bit hash for each shingle. |
| **Reason** | SHA-256 is stable and auditable. 64-bit hash is useful for fast indexing and approximate similarity workflows. |
| **Consequence** | Slightly larger Parquet output, but better downstream flexibility. |

### ADR-009: Defer Embeddings from the POC

| Field | Decision |
|-------|----------|
| **Status** | Accepted |
| **Context** | Vector embeddings are useful for semantic similarity but are not required for deterministic near-duplicate detection. |
| **Decision** | Do not use embeddings in the POC. |
| **Reason** | Shingling, hashing, MinHash, and LSH are more explainable and cost-efficient for document fingerprinting. |
| **Consequence** | Semantic paraphrase detection is out of scope for the POC. It can be added later as a separate enrichment path. |

### ADR-010: Include MinHash and LSH Indexing in POC Scope

| Field | Decision |
|-------|----------|
| **Status** | Accepted |
| **Context** | The POC must validate the end-to-end fingerprinting and near-duplicate candidate lookup flow, not only shingle generation. |
| **Decision** | Generate MinHash signatures and build an LSH index as part of the POC scope. |
| **Reason** | Without MinHash and LSH, the POC would stop before proving the similarity matching architecture. |
| **Consequence** | The POC will include extraction, shingling, signature generation, LSH indexing, and candidate lookup. |

### ADR-011: Support Document Partitioning and Final Merge

| Field | Decision |
|-------|----------|
| **Status** | Accepted |
| **Context** | Large documents may need to be split for distributed processing, and future scale-out execution may process partitions independently. |
| **Decision** | Design partition-aware assets that generate partition-level shingles/signatures and then merge them into a final document-level signature. |
| **Reason** | Partitioning enables distributed execution while keeping a deterministic final document identity and signature. |
| **Consequence** | The pipeline must track `partition_id`, `partition_count`, and merge status in metadata and signature artifacts. |

### ADR-012: Retain Signatures, Not Raw Shingles, for DLP-Safe Operation

| Field | Decision |
|-------|----------|
| **Status** | Accepted |
| **Context** | Raw shingle text can expose sensitive document fragments if stored long term. |
| **Decision** | Retain document-level hash signatures, MinHash signatures, and LSH index artifacts after processing; delete or expire raw shingle artifacts by default. |
| **Reason** | This reduces DLP exposure while preserving the data needed for similarity detection. |
| **Consequence** | Debug mode may retain shingle text under controlled access, but production DLP-safe mode should not. |

---

## 17. ADR Summary Table — Grouped by Workflow Step

| Step | Process Name | Library Used | Key Process | Logic |
|------|-------------|-------------|-------------|-------|
| 1. Input discovery | `DocumentDiscoveryProcessor` | `pathlib`, Dagster config | Discover source documents from input folder or configured URI | Scan configured input path, filter supported extensions, create source document asset list |
| 2. Basic metadata | `DocumentMetadataExtractor` | `os`, `pathlib`, `python-magic` | Extract file name, extension, MIME type, size, modified date | Read filesystem metadata only. Avoid expensive document profiling |
| 3. Checksum | `DocumentChecksumProcessor` | `hashlib` | Generate SHA-256 checksum | Read file as bytes in chunks and calculate SHA-256. Use checksum as stable document ID |
| 4. Metadata output | `MetadataJsonWriter` | `json` | Write metadata sidecar JSON | Store document-level metadata as `{document_name_or_doc_fqdn}.metadata.json` |
| 5. Text extraction interface | `DocumentTextExtractor` | Python ABC/interface | Define common extraction contract | Dagster step calls interface, not concrete parser implementation |
| 6. Default text extraction | `TikaDocumentTextExtractor` | Apache Tika | Extract text and metadata from major document formats | Use Tika as default POC extractor because it supports broad file formats through one interface |
| 7. Future extraction option | `DoclingDocumentTextExtractor` | Docling | Extract structured content, layout-aware text, Markdown/JSON | Use later if better layout, reading order, tables, or structured export is needed |
| 8. Future Markdown extraction option | `MarkItDownDocumentTextExtractor` | MarkItDown | Convert documents to Markdown-oriented text | Use later for LLM-ready Markdown conversion and common Office/PDF formats |
| 9. OCR detection | `OcrDecisionProcessor` | Custom logic | Decide whether OCR is required | If extracted text length is below threshold or OCR flag is enabled, route to OCR |
| 10. OCR processing | `OcrProcessor` | OCRmyPDF / Tesseract | Extract text from scanned/image-based documents | Apply OCR only when required. Avoid unnecessary OCR cost |
| 11. Raw text output | `RawTextWriter` | Python file I/O | Persist raw extracted text | Write `{document_name_or_doc_fqdn}.extracted.txt` for traceability/debugging |
| 12. Text normalization | `TextNormalizer` | `re`, `unicodedata`, optional NLTK | Normalize text for deterministic shingling | Lowercase, normalize Unicode, clean whitespace, optionally remove punctuation and stopwords |
| 13. Normalized text output | `NormalizedTextWriter` | Python file I/O | Persist normalized text | Write `{document_name_or_doc_fqdn}.normalized.txt` |
| 14. Tokenization | `TokenizerProcessor` | Custom regex / optional NLTK | Split normalized text into tokens | Use simple deterministic tokenization. Keep numbers by default |
| 15. Shingle generation | `WordShingleGenerator` | Custom Python | Generate word-level shingles | Sliding window over tokens. Default shingle size = 5 words |
| 16. Shingle hashing | `ShingleHashProcessor` | `hashlib`, `xxhash` | Generate stable and fast shingle hashes | SHA-256 for auditability; xxhash64 for fast matching/indexing |
| 17. Shingle DataFrame | `ShingleFrameBuilder` | Polars or Pandas | Build tabular shingle records | Create one row per shingle with document ID, offsets, text, and hashes |
| 18. Temporary Parquet output | `ShingleParquetWriter` | PyArrow / Polars | Write temporary columnar shingle output | Write `{document_name_or_doc_fqdn}_shingle.parquet` during processing; mark artifact for deletion/expiry after signatures are generated |
| 19. Signature retention | `DocumentSignatureWriter` | `json` / PyArrow | Persist retained document-level signatures | Store hash signature, MinHash signature, shingle counts, and signature metadata without raw shingle text |
| 20. Shingle cleanup | `ShingleRetentionProcessor` | Dagster asset cleanup / filesystem policy | Delete or expire sensitive intermediate shingles | Remove raw `shingle_text` artifacts after successful signature and LSH materialization when DLP-safe mode is enabled |
| 21. Asset materialization | `DagsterAssetMaterializer` | Dagster | Register output files as Dagster materialized assets | Attach row count, signature path, document ID, and processing status as metadata |
| 22. MinHash | `MinHashSignatureBuilder` | datasketch | Generate MinHash signatures from shingles | Convert shingle hashes into MinHash signature for approximate Jaccard similarity. Included in POC |
| 23. LSH | `LshIndexBuilder` | datasketch | Build candidate lookup index | Use LSH to identify possible similar documents. Included in POC |
| 24. Similarity scoring | `SimilarityScorer` | Custom / datasketch | Calculate final similarity score | LSH generates candidates; final score uses actual shingle Jaccard similarity. Included in POC |
| 25. Partitioning | `DocumentPartitionProcessor` | Custom / Dagster partitions | Split large documents into processing partitions | Generate partition-level shingles/signatures to enable distributed processing |
| 26. Partition merge | `PartitionSignatureMerger` | Custom / datasketch | Merge partition-level outputs | Merge sorted unique shingle hash sets and MinHash states into final document-level signature |

---

## 18. Suggested Project Structure

```
document-fingerprint-pipeline/
  README.md
  pyproject.toml
  dagster.yaml
  workspace.yaml

  src/
    docfp/
       __init__.py
       models/
         document_metadata.py
         extracted_text.py
         normalized_text.py
         shingle_record.py
       interfaces/
         document_text_extractor.py
         ocr_processor.py
         normalizer.py
         shingle_generator.py
         shingle_hasher.py
         artifact_writer.py
       extractors/
         tika_extractor.py
         docling_extractor.py
         markitdown_extractor.py
       processors/
         metadata_extractor.py
         checksum_processor.py
         ocr_decision_processor.py
         text_normalizer.py
         tokenizer.py
         word_shingle_generator.py
         shingle_hash_processor.py
         minhash_signature_builder.py
         lsh_index_builder.py
         document_partition_processor.py
         partition_signature_merger.py
         shingle_retention_processor.py
       writers/
         metadata_json_writer.py
         text_writer.py
         shingle_parquet_writer.py
         document_signature_writer.py
       dagster_defs/
         assets.py
         jobs.py
         resources.py
         schedules.py
  input/
  output/
    metadata/
    text/
    normalized/
    shingles/
    signatures/
    indexes/
    partitions/
    logs/
  tests/
```

---

## 19. POC Execution Flow

```
dagster dev
  -> Materialize source_document
  -> Materialize document_metadata_json
  -> Materialize raw_extracted_text
  -> Materialize normalized_text
  -> Materialize document_shingles
  -> Materialize temporary_document_shingle_parquet
  -> Materialize document_hash_signature
  -> Materialize document_minhash_signature
  -> Materialize lsh_index
  -> Materialize shingle_retention_cleanup
```

---

## 20. Success Criteria

| ID | Success Criteria |
|----|-----------------|
| SC-001 | Pipeline can process PDF, DOCX, PPTX, and TXT files. |
| SC-002 | Pipeline generates one metadata JSON per document. |
| SC-003 | Pipeline generates one shingle Parquet per document. |
| SC-004 | Pipeline can rerun failed steps in Dagster. |
| SC-005 | Text extraction implementation can be swapped without changing downstream processors. |
| SC-006 | Shingle output contains stable document ID and shingle hashes. |
| SC-007 | Normalization and shingling are deterministic and testable. |
| SC-008 | POC avoids vector embedding dependency. |
| SC-009 | POC produces retained MinHash signatures and an LSH index. |
| SC-010 | POC can delete or expire raw shingle artifacts after signature generation. |
| SC-011 | POC design supports document partitioning and final partition merge. |

---

## 21. Open Questions

| ID | Question |
|----|----------|
| OQ-001 | What retention period should be used for temporary shingle Parquet artifacts before deletion? |
| OQ-002 | Should page number and section offsets be mandatory or best-effort? |
| OQ-003 | Should OCR be automatic or controlled through config? |
| OQ-004 | Should old `.doc` files be processed directly through Tika or converted first using LibreOffice? |
| OQ-006 | Should output be partitioned by document ID, source system, or processing date? |
| OQ-007 | Should stopword removal be enabled by default? |
| OQ-008 | Should numbers be preserved by default for contracts, reports, and technical documents? |

---

## 22. Recommended POC Decision

- Use Dagster for orchestration.
- Use Apache Tika as the default extraction engine.
- Create a clean `DocumentTextExtractor` interface.
- Keep Docling and MarkItDown as future swappable extractors.
- Use deterministic normalization.
- Generate 5-word shingles.
- Generate SHA-256 and xxhash64 for every shingle.
- Store metadata as JSON and shingle output as temporary Parquet.
- Retain document-level hash signatures and MinHash signatures.
- Build and persist the LSH index in the POC.
- Delete or expire raw shingle files after successful signature/index materialization in DLP-safe mode.
- Design now for document partitioning and final partition merge.
- Defer vector embeddings from the POC.

---

*Source: `document_fingerprinting_brd_adr_dagster_updated_convertedToPDF.pdf` — converted to Markdown 2026-05-05*
