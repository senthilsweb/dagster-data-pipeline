"""
File Name: shingle_hasher.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: ShingleHasher ABC — interface for computing shingle hash values
             (FR-012, FR-013, ADR-008).

Requirements:
- Python 3.12+
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ShingleHasher(ABC):
    """Abstract base class for shingle hashing strategies.

    Implementations must return deterministic hashes: same text → same output
    across all runs and environments.
    """

    @abstractmethod
    def hash_sha256(self, text: str) -> str:
        """Compute a SHA-256 hex digest of the shingle text.

        Args:
            text: Shingle text string.

        Returns:
            Lowercase hex string (64 chars).
        """

    @abstractmethod
    def hash64(self, text: str) -> int:
        """Compute a fast 64-bit hash of the shingle text.

        Args:
            text: Shingle text string.

        Returns:
            64-bit unsigned integer hash value.
        """
