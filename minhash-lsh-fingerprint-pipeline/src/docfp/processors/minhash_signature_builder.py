"""
File Name: minhash_signature_builder.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: MinHashSignatureBuilder — generates a datasketch MinHash signature
             from a document's shingle hash set (FR-023, ADR-010).

Requirements:
- datasketch>=1.6
- Python 3.12+
"""

from __future__ import annotations

import logging
import os
from datetime import datetime

import structlog
from datasketch import MinHash

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

DEFAULT_NUM_PERM = 128


class MinHashSignatureBuilder:
    """Build a MinHash signature from a collection of shingle hashes.

    Args:
        num_perm: Number of permutations for the MinHash sketch. Default 128.

    Returns:
        datasketch.MinHash object representing the document's MinHash signature.
    """

    def __init__(self, num_perm: int = DEFAULT_NUM_PERM) -> None:
        self.num_perm = num_perm

    def build(self, shingle_hashes: list[int], document_id: str) -> MinHash:
        """Create a MinHash sketch from a list of 64-bit shingle hashes.

        Args:
            shingle_hashes: List of xxhash64 integer values (one per shingle).
            document_id: SHA-256 document ID (used for logging).

        Returns:
            datasketch.MinHash instance representing the document signature.
        """
        mh = MinHash(num_perm=self.num_perm)
        for h in shingle_hashes:
            mh.update(h.to_bytes(8, byteorder="little"))
        log.info(
            "minhash_built",
            document_id=document_id,
            shingle_count=len(shingle_hashes),
            num_perm=self.num_perm,
        )
        return mh
