## ADDED Requirements

### Requirement: Word shingle generation

- The system SHALL generate word-level shingles using a sliding window over tokenized normalized text (FR-011, ADR-005).
- The default shingle size SHALL be 5 words; this SHALL be configurable per pipeline run.
- Each shingle SHALL include: `document_id`, `partition_id`, `partition_count`, `source_uri`, `file_name`, `page_no`, `section_id`, `shingle_id`, `shingle_text`, `token_start`, `token_end`, `char_start`, `char_end`, and `normalization_version` fields.

#### Scenario: 5-word sliding window
- GIVEN normalized text `"the quick brown fox jumps over the lazy dog"`
- WHEN shingle generation runs with size=5
- THEN shingles `["the quick brown fox jumps", "quick brown fox jumps over", ...]` are produced

### Requirement: Shingle hashing

- The system SHALL generate a **SHA-256 hash** (`shingle_hash_sha256`) for each shingle for stable auditability (FR-012, ADR-008).
- The system SHALL generate a **fast 64-bit hash** (`shingle_hash64`) for each shingle for indexing and approximate similarity (FR-013, ADR-008).

#### Scenario: Deterministic hashes
- GIVEN the same shingle text processed twice
- WHEN hashing runs
- THEN both SHA-256 and 64-bit hashes are identical across runs

### Requirement: Temporary shingle Parquet output

- The system SHALL write shingle records to `{document_name}_shingle.parquet` using PyArrow (FR-014, ADR-006).
- The Parquet schema SHALL include all columns defined in BRD section 11.
- The shingle Parquet file SHALL be marked as a temporary artifact subject to deletion after signature generation (ADR-006, FR-022).

#### Scenario: Parquet schema conformance
- GIVEN a processed document
- WHEN the shingle Parquet is written
- THEN the file contains columns `document_id`, `shingle_text`, `shingle_hash_sha256`, `shingle_hash64`, `created_at_utc` at minimum
