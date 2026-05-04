# dagster-orchestration Specification

## Purpose
TBD - created by archiving change document-fingerprinting-pipeline. Update Purpose after archive.
## Requirements
### Requirement: Dagster asset structure

- The system SHALL model each pipeline processing stage as an independently materializable Dagster asset or op (FR-016, ADR-001).
- Asset names SHALL match the BRD section 8.1 asset map: `source_document`, `document_metadata_json`, `raw_extracted_text`, `ocr_extracted_text`, `normalized_text`, `document_shingles`, `document_shingle_hashes`, `document_shingle_parquet`, `document_hash_signature`, `document_minhash_signature`, `lsh_index`, `document_fingerprint_summary`.
- Asset definitions SHALL reside in `src/docfp/dagster_defs/assets.py`.

#### Scenario: Step-level rematerialization
- GIVEN the `normalized_text` asset fails on one document
- WHEN the Dagster step is rerun from the UI or CLI
- THEN only the failed step re-executes without restarting the full pipeline

### Requirement: Observability and logging

- The system SHALL log processing status and errors for every step using `structlog` (FR-017, NFR-010).
- Each Dagster asset materialization SHALL attach metadata: `document_id`, `row_count` (where applicable), signature path, and processing status.
- Log files SHALL follow the timestamped naming convention established in the project (`{script_name}_{YYYYMMDD_HHMMSS}.log`).

#### Scenario: Materialization metadata visible in Dagster UI
- GIVEN a successfully materialized `document_hash_signature` asset
- WHEN the asset is inspected in the Dagster UI
- THEN `document_id`, `signature_path`, and `status: completed` appear in the materialization metadata

### Requirement: Batch and isolation support

- The system SHALL support batch processing of multiple documents in a single pipeline run (FR-018).
- Each document SHALL be processed in isolation so a failure in one document does not block others (FR-019, NFR-004).

#### Scenario: Batch processing isolation
- GIVEN a batch of 5 documents where document 3 fails text extraction
- WHEN the pipeline runs
- THEN documents 1, 2, 4, and 5 complete successfully and document 3 is flagged as failed without aborting the batch

