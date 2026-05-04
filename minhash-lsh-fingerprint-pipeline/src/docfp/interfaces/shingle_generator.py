"""
File Name: shingle_generator.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: ShingleGenerator ABC — interface for sliding-window shingle
             generation (FR-011, ADR-005).

Requirements:
- Python 3.12+
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from docfp.models.shingle_record import ShingleRecord


class ShingleGenerator(ABC):
    """Abstract base class for shingle generation strategies.

    Args:
        document_id: SHA-256 identifier for the source document.
        source_uri: Absolute path or URI of the source document.
        file_name: Original file name.
        tokens: List of normalized tokens to shingle over.
        partition_id: Zero-based partition index.
        partition_count: Total partitions for this document.

    Returns:
        List of ShingleRecord objects.
    """

    @abstractmethod
    def generate(
        self,
        document_id: str,
        source_uri: str,
        file_name: str,
        tokens: list[str],
        partition_id: int = 0,
        partition_count: int = 1,
    ) -> list[ShingleRecord]:
        """Generate shingles from a token list.

        Args:
            document_id: SHA-256 identifier for the source document.
            source_uri: Absolute path or URI of the source document.
            file_name: Original file name with extension.
            tokens: Normalized token list to slide the window over.
            partition_id: Zero-based index of this partition.
            partition_count: Total number of partitions.

        Returns:
            List of ShingleRecord with text and hash fields populated.
        """
