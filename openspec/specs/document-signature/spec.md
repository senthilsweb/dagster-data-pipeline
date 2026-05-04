# document-signature Specification

## Purpose
TBD - created by archiving change document-fingerprinting-pipeline. Update Purpose after archive.
## Requirements
### Requirement: Document-level hash signature

- The system SHALL generate a `hash_signature_sha256` derived from the sorted set of unique shingle hashes for the document (FR-021).
- The system SHALL persist the signature to `{document_name}.hash_signature.json` (FR-021).
- The retained signature artifact SHALL include: `document_id`, `source_uri`, `file_name`, `signature_version`, `shingle_size`, `total_shingle_count`, `unique_shingle_hash_count`, `hash_signature_sha256`, `minhash_signature`, `lsh_bucket_keys`, `partition_merge_status`, and `created_at_utc` (BRD section 11.1).

#### Scenario: Signature derived from shingle hashes
- GIVEN a document with 120 shingles of which 95 are unique
- WHEN the signature is generated
- THEN `unique_shingle_hash_count` equals 95 and `hash_signature_sha256` is the SHA-256 of the sorted unique hash values

### Requirement: DLP-safe shingle retention

- The system SHALL delete or expire `{document_name}_shingle.parquet` after successful signature and LSH materialization when DLP-safe mode is enabled (FR-022, ADR-012).
- A controlled **debug mode** flag SHALL allow raw shingle text retention under explicit configuration.
- Production DLP-safe mode SHALL NOT retain raw shingle text by default.

#### Scenario: Shingle cleanup in DLP-safe mode
- GIVEN DLP-safe mode is enabled and signature generation succeeded
- WHEN the shingle retention processor runs
- THEN `{document_name}_shingle.parquet` is deleted from the output folder

#### Scenario: Shingle retained in debug mode
- GIVEN debug mode is explicitly enabled
- WHEN the shingle retention processor runs
- THEN `{document_name}_shingle.parquet` is retained and not deleted

