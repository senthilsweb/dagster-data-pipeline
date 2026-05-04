## ADDED Requirements

### Requirement: OCR routing decision

- The system SHALL apply OCR when extracted text length is below a configured threshold OR when `ocr_enabled` is explicitly set to `true` in pipeline configuration (FR-009).
- The OCR decision processor SHALL route documents to the OCR path without modifying the extractor interface contract.

#### Scenario: OCR triggered on empty extraction
- GIVEN a scanned PDF where Tika returns empty text
- WHEN the OCR decision processor evaluates the extraction result
- THEN the document is routed to `OcrProcessor`

#### Scenario: OCR skipped for text-native document
- GIVEN a DOCX file with rich body text
- WHEN the OCR decision processor evaluates the extraction result
- THEN OCR is not applied and `ocr_applied` remains `False`

### Requirement: OCR processing

- The system SHALL use OCRmyPDF or Tesseract to extract text from scanned or image-based documents (FR-009).
- The system SHALL record `ocr_applied: true` in the metadata JSON when OCR is used.
- OCR SHALL only be applied when required to avoid unnecessary processing cost (ADR-004).

#### Scenario: OCR result captured
- GIVEN a scanned document routed to OCR
- WHEN `OcrProcessor` runs
- THEN extracted text is non-empty and `{document_name}.extracted.txt` is written with OCR-sourced content
