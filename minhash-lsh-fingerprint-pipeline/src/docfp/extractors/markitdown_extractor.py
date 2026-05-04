"""
File Name: markitdown_extractor.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: MarkItDownDocumentTextExtractor — stub for future MarkItDown-based
             extraction (ADR-003).  Not implemented for POC.

Requirements:
- Python 3.12+
"""

from __future__ import annotations

from docfp.interfaces.document_text_extractor import DocumentTextExtractor
from docfp.models.extracted_text import ExtractedDocumentText

EXTRACTION_ENGINE = "markitdown"


class MarkItDownDocumentTextExtractor(DocumentTextExtractor):
    """Stub: MarkItDown-based text extractor (not implemented for POC).

    Args:
        source_uri: Absolute path or URI of the document.

    Returns:
        Raises NotImplementedError.
    """

    def extract(self, source_uri: str) -> ExtractedDocumentText:
        """Not implemented — placeholder for MarkItDown extraction.

        Args:
            source_uri: Absolute path or URI of the document.

        Returns:
            Raises NotImplementedError.
        """
        raise NotImplementedError("MarkItDownDocumentTextExtractor is not implemented in POC.")
