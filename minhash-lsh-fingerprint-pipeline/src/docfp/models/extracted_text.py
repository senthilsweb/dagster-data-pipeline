"""
File Name: extracted_text.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: ExtractedDocumentText dataclass — returned by every DocumentTextExtractor
             implementation.  Written to {doc}.extracted.txt.

Requirements:
- Python 3.12+
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExtractedDocumentText:
    """Container for raw text extracted from a document.

    Args:
        document_id: SHA-256 checksum of the source file.
        source_uri: Absolute path or URI of the source document.
        text: Full extracted text body.
        metadata: Extractor-specific metadata (page count, author, etc.).
        pages: Per-page text chunks — list of {'page': int, 'text': str}.
        extraction_engine: Name of the engine used (e.g. 'apache-tika').
        ocr_applied: True when OCR was the source of the text.

    Returns:
        ExtractedDocumentText instance.
    """

    document_id: str
    source_uri: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    pages: list[dict[str, Any]] = field(default_factory=list)
    extraction_engine: str = "apache-tika"
    ocr_applied: bool = False
