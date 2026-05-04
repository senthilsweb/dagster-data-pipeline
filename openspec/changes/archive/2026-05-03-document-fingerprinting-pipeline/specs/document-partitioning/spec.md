## ADDED Requirements

### Requirement: Document partitioning

- The system SHALL support splitting large documents into numbered partitions for distributed processing (FR-025, ADR-011).
- Each partition SHALL carry `partition_id` and `partition_count` fields through all processing steps.
- Partition-level shingles and signatures SHALL be generated independently per partition.

#### Scenario: Partition metadata propagated
- GIVEN a large document split into 4 partitions
- WHEN each partition is processed
- THEN each shingle record and signature artifact contains the correct `partition_id` (0–3) and `partition_count` (4)

### Requirement: Partition signature merge

- The system SHALL merge partition-level sorted unique shingle hash sets and MinHash states into a final document-level signature (FR-026, ADR-011).
- The `partition_merge_status` field in the signature artifact SHALL indicate `"single-partition"` or `"merged-partition"`.

#### Scenario: Merged signature stable across re-runs
- GIVEN 4 partition-level signatures for the same document
- WHEN `PartitionSignatureMerger` runs
- THEN the merged `hash_signature_sha256` is identical to a single-pass signature of the same document

#### Scenario: Single-partition document not merged
- GIVEN a small document that fits in one partition
- WHEN processing completes
- THEN `partition_merge_status` equals `"single-partition"` and no merge step runs
