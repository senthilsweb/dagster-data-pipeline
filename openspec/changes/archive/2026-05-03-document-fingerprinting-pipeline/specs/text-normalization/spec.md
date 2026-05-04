## ADDED Requirements

### Requirement: Deterministic text normalization

- The system SHALL normalize extracted text using deterministic rules: lowercase conversion, Unicode normalization (NFC), whitespace cleanup, and punctuation handling (FR-010, ADR-004).
- The system SHALL support optional stopword removal configurable per pipeline run.
- The system SHALL NOT use lemmatization, entity extraction, or embeddings in the POC (ADR-009, NFR-006).
- Normalization logic SHALL be implemented as a `TextNormalizer` class behind the `Normalizer` interface for testability (NFR-002, NFR-003).

#### Scenario: Lowercase and whitespace normalization
- GIVEN extracted text `"  Hello   World.\n\tFoo  "`
- WHEN `TextNormalizer` processes it
- THEN output is `"hello world foo"` (or equivalent cleaned form)

#### Scenario: Deterministic reproducibility
- GIVEN the same raw text input processed twice
- WHEN normalization runs both times
- THEN both outputs are byte-identical

### Requirement: Normalized text output

- The system SHALL write normalized text to `{document_name}.normalized.txt` (FR-010).
- The normalization version SHALL be recorded in the metadata JSON as `normalization_version`.

#### Scenario: Normalized text file created
- GIVEN `contract_v1.extracted.txt` exists
- WHEN normalization completes
- THEN `contract_v1.normalized.txt` is written and `normalization_version` is set in metadata
