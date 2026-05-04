"""
File Name: document_text_extractor.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: DocumentTextExtractor ABC — swap extraction engines without
             changing any pipeline or processor code (ADR-003).

Requirements:
- Python 3.12+
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from docfp.models.extracted_text import ExtractedDocumentText


class DocumentTextExtractor(ABC):
    """Abstract base class for all document text extraction engines.

    Args:
        source_uri: Absolute path or URI of the document to extract text from.

    Returns:
        ExtractedDocumentText containing raw text, per-page chunks, and
        extraction metadata.
    """

    @abstractmethod
    def extract(self, source_uri: str) -> ExtractedDocumentText:
        """Extract text from a document at the given URI.

        Args:
            source_uri: Absolute path or URI of the source document.

        Returns:
            ExtractedDocumentText with text, pages, engine name, and
            ocr_applied flag.
        """
