"""
File Name: normalized_text.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: NormalizedText dataclass — output of TextNormalizer, written to
             {doc}.normalized.txt.

Requirements:
- Python 3.12+
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NormalizedText:
    """Container for deterministically normalized text.

    Args:
        document_id: SHA-256 checksum of the source file.
        source_uri: Absolute path or URI of the source document.
        text: Normalized text — lowercase, unicode-NFC, cleaned whitespace.
        normalization_version: Identifier of the rule set applied (e.g. 'v1').
        token_count: Number of whitespace-split tokens after normalization.

    Returns:
        NormalizedText instance.
    """

    document_id: str
    source_uri: str
    text: str
    normalization_version: str = "v1"
    token_count: int = 0
