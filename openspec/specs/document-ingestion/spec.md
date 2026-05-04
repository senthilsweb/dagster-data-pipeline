# document-ingestion Specification

## Purpose
TBD - created by archiving change document-fingerprinting-pipeline. Update Purpose after archive.
## Requirements
### Requirement: Input discovery

- The system SHALL accept document files from a configured input folder or URI (FR-001).
- The system SHALL filter files by supported extension: `.pdf`, `.doc`, `.docx`, `.ppt`, `.pptx`, `.txt`, `.html`, `.xls`, `.xlsx`.
- The system SHALL represent each discovered document as a Dagster `source_document` asset.

#### Scenario: Discover supported documents
- GIVEN a folder containing `contract.docx`, `report.pdf`, `image.png`
- WHEN the discovery processor runs
- THEN `contract.docx` and `report.pdf` are discovered and `image.png` is ignored

### Requirement: Metadata extraction

- The system SHALL extract file name, extension, MIME type, size in bytes, and modified date without expensive profiling (FR-002, FR-004).
- The system SHALL calculate a SHA-256 checksum and use it as the stable `document_id` (FR-003).
- The system SHALL write a metadata JSON sidecar named `{document_name}.metadata.json` (FR-015).
- The metadata JSON SHALL conform to the schema defined in BRD section 10.

#### Scenario: Metadata JSON output
- GIVEN `contract_template_v1.docx` as input
- WHEN the metadata extractor and checksum processor run
- THEN `contract_template_v1.metadata.json` is written containing `document_id`, `checksum_sha256`, `file_extension`, `mime_type`, `size_bytes`, and `pipeline_name`

#### Scenario: Stable document ID
- GIVEN the same file processed twice with unchanged content
- WHEN checksums are calculated
- THEN both runs produce the same `document_id` value

