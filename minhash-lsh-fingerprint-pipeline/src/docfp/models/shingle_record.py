"""
File Name: shingle_record.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: ShingleRecord dataclass — one row in the {doc}_shingle.parquet file.
             Schema mirrors BRD §11 columnar shingle artifact.

Requirements:
- Python 3.12+
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ShingleRecord:
    """One shingle row persisted to Parquet.

    Args:
        document_id: SHA-256 checksum of the source file.
        partition_id: Zero-based partition index (0 for single-partition docs).
        partition_count: Total partitions the document was split into.
        source_uri: Absolute path or URI of the source document.
        file_name: Original file name with extension.
        page_no: Source page number (0 if not page-aware).
        section_id: Section identifier within the page (0 if not applicable).
        shingle_id: Zero-based shingle index within this document/partition.
        shingle_text: Raw shingle text (N consecutive tokens).
        shingle_hash64: xxhash64 of shingle_text for fast indexing.
        shingle_hash_sha256: SHA-256 hex digest of shingle_text for auditability.
        token_start: Index of the first token in the original token list.
        token_end: Index of the last token (inclusive).
        char_start: Char offset of the first token in the normalized text.
        char_end: Char offset after the last token in the normalized text.
        normalization_version: Normalization rule set applied.
        created_at_utc: ISO-8601 UTC timestamp of shingle generation.

    Returns:
        ShingleRecord instance.
    """

    document_id: str
    partition_id: int
    partition_count: int
    source_uri: str
    file_name: str
    page_no: int
    section_id: int
    shingle_id: int
    shingle_text: str
    shingle_hash64: int
    shingle_hash_sha256: str
    token_start: int
    token_end: int
    char_start: int
    char_end: int
    normalization_version: str
    created_at_utc: str
