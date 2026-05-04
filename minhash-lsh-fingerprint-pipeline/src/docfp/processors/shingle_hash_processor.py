"""
File Name: shingle_hash_processor.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: ShingleHashProcessor — computes SHA-256 and xxhash64 for each
             shingle in-place (FR-012, FR-013, ADR-008).

Requirements:
- xxhash>=3.4
- Python 3.12+
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime

import structlog
import xxhash

from docfp.interfaces.shingle_hasher import ShingleHasher
from docfp.models.shingle_record import ShingleRecord

script_name = os.path.splitext(os.path.basename(__file__))[0]
log_filename = f"{script_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(filename=log_filename, level=logging.INFO, format="%(message)s")
structlog.configure(
    logger_factory=structlog.stdlib.LoggerFactory(),
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)
log = structlog.get_logger()


class ShingleHashProcessor(ShingleHasher):
    """Compute SHA-256 and xxhash64 for shingle text.

    Methods can be used standalone or via hash_records() to fill a list
    of ShingleRecord objects in place.
    """

    def hash_sha256(self, text: str) -> str:
        """Compute SHA-256 hex digest of shingle text.

        Args:
            text: Shingle text string.

        Returns:
            Lowercase 64-char hex string.
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def hash64(self, text: str) -> int:
        """Compute xxhash 64-bit integer hash of shingle text.

        Args:
            text: Shingle text string.

        Returns:
            64-bit unsigned integer (xxh64).
        """
        return xxhash.xxh64(text.encode("utf-8")).intdigest()

    def hash_records(self, records: list[ShingleRecord]) -> list[ShingleRecord]:
        """Fill shingle_hash_sha256 and shingle_hash64 on a list of ShingleRecords.

        Args:
            records: List of ShingleRecord with shingle_text populated.

        Returns:
            The same list with hash fields filled in (mutated in place).
        """
        for rec in records:
            rec.shingle_hash_sha256 = self.hash_sha256(rec.shingle_text)
            rec.shingle_hash64 = self.hash64(rec.shingle_text)
        log.info("shingles_hashed", count=len(records))
        return records
