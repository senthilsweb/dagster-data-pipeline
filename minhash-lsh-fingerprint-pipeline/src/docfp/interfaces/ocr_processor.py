"""
File Name: ocr_processor.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: OcrProcessor ABC — OCR back-end interface. Concrete implementations
             wrap OCRmyPDF or Tesseract (FR-009).

Requirements:
- Python 3.12+
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from docfp.models.extracted_text import ExtractedDocumentText


class OcrProcessor(ABC):
    """Abstract base class for OCR processing engines.

    Args:
        source_uri: Absolute path or URI of the document requiring OCR.
        document_id: Pre-computed SHA-256 document identifier.

    Returns:
        ExtractedDocumentText with ocr_applied=True.
    """

    @abstractmethod
    def run_ocr(self, source_uri: str, document_id: str) -> ExtractedDocumentText:
        """Run OCR on a document and return extracted text.

        Args:
            source_uri: Absolute path or URI of the source document.
            document_id: SHA-256 identifier for the document.

        Returns:
            ExtractedDocumentText with ocr_applied=True.
        """
