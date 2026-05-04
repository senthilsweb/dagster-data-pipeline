"""
File Name: normalizer.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: Normalizer ABC — deterministic text normalization interface (FR-010,
             ADR-004).

Requirements:
- Python 3.12+
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from docfp.models.normalized_text import NormalizedText


class Normalizer(ABC):
    """Abstract base class for text normalization.

    Implementations must be deterministic: the same input MUST always produce
    the same output regardless of run order or environment.

    Args:
        document_id: SHA-256 identifier for the source document.
        source_uri: Absolute path or URI of the source document.
        text: Raw extracted text to normalize.

    Returns:
        NormalizedText instance.
    """

    @abstractmethod
    def normalize(self, document_id: str, source_uri: str, text: str) -> NormalizedText:
        """Normalize raw extracted text.

        Args:
            document_id: SHA-256 identifier for the source document.
            source_uri: Absolute path or URI of the source document.
            text: Raw extracted text string.

        Returns:
            NormalizedText with cleaned, lowercase, unicode-normalized text.
        """
