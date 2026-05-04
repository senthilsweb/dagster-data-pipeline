# text-extraction Specification

## Purpose
TBD - created by archiving change document-fingerprinting-pipeline. Update Purpose after archive.
## Requirements
### Requirement: Pluggable extractor interface

- The system SHALL define a `DocumentTextExtractor` ABC with a single `extract(source_uri: str) → ExtractedDocumentText` method (FR-006).
- Dagster assets SHALL depend on the `DocumentTextExtractor` interface, not on any concrete implementation (ADR-003).
- The system SHALL allow `TikaDocumentTextExtractor`, `DoclingDocumentTextExtractor`, and `MarkItDownDocumentTextExtractor` to be registered and swapped without changing pipeline logic (FR-008).

#### Scenario: Interface swap
- GIVEN the pipeline is configured with `TikaDocumentTextExtractor`
- WHEN the configuration is changed to `DoclingDocumentTextExtractor`
- THEN all downstream Dagster assets receive `ExtractedDocumentText` in the same shape without code changes

### Requirement: Default POC extraction

- The system SHALL use Apache Tika as the default POC text extraction engine (FR-007, ADR-002).
- The system SHALL extract text from PDF, DOC, DOCX, PPT, PPTX, TXT, HTML, XLS, and XLSX formats (FR-005).
- The system SHALL write raw extracted text to `{document_name}.extracted.txt` for traceability (FR-005).
- The `ExtractedDocumentText` dataclass SHALL include `document_id`, `source_uri`, `text`, `metadata`, `pages`, `extraction_engine`, and `ocr_applied` fields.

#### Scenario: PDF text extraction
- GIVEN `report.pdf` as input
- WHEN `TikaDocumentTextExtractor.extract()` runs
- THEN `report.extracted.txt` is written and `ocr_applied` is `False`

#### Scenario: Extraction engine recorded in metadata
- GIVEN a document processed with Tika
- WHEN the metadata JSON is written
- THEN `text_extraction_engine` equals `"apache-tika"`

