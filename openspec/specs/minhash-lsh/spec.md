# minhash-lsh Specification

## Purpose
TBD - created by archiving change document-fingerprinting-pipeline. Update Purpose after archive.
## Requirements
### Requirement: MinHash signature generation

- The system SHALL generate a MinHash signature from document shingle hashes using `datasketch` (FR-023, ADR-010).
- MinHash signatures SHALL be persisted to `{document_name}.minhash.json` as part of the retained document signature artifact.
- MinHash signatures SHALL enable approximate Jaccard similarity estimation between documents without comparing raw shingle text.

#### Scenario: MinHash generated per document
- GIVEN a document with shingle hashes computed
- WHEN `MinHashSignatureBuilder` runs
- THEN `{document_name}.minhash.json` is written containing the MinHash signature values

### Requirement: LSH index build and persistence

- The system SHALL build and persist an LSH index using `datasketch` for candidate document lookup (FR-024, ADR-010).
- The LSH index SHALL be persisted as `corpus_lsh_index.pkl` or `corpus_lsh_index.parquet`.
- The LSH index SHALL support querying for candidate near-duplicate documents given a query MinHash signature.

#### Scenario: LSH candidate lookup
- GIVEN two near-duplicate documents indexed in the LSH
- WHEN the LSH index is queried with the MinHash of document A
- THEN document B appears as a candidate result

### Requirement: Similarity scoring

- The system SHALL calculate a final similarity score using LSH-generated candidates and actual shingle Jaccard similarity (ADR-010).
- The similarity scorer SHALL NOT use vector embeddings (ADR-009).

#### Scenario: Score reflects shingle overlap
- GIVEN document A and document B sharing 80% of shingles
- WHEN the similarity scorer runs
- THEN the Jaccard similarity score is approximately 0.80

