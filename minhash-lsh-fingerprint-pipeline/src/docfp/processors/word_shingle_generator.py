"""
File Name: word_shingle_generator.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: WordShingleGenerator — sliding-window word shingle generation
             (FR-011, ADR-005).  Default shingle size is 5 words.

Requirements:
- Python 3.12+
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import structlog

from docfp.interfaces.shingle_generator import ShingleGenerator
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

DEFAULT_SHINGLE_SIZE = 5
NORMALIZATION_VERSION = "v1"


class WordShingleGenerator(ShingleGenerator):
    """Generate word-level shingles using a sliding window.

    Args:
        shingle_size: Number of words per shingle. Default is 5.

    Returns:
        List of ShingleRecord with text populated but hashes left empty
        (hashes are filled by ShingleHashProcessor in the next step).
    """

    def __init__(self, shingle_size: int = DEFAULT_SHINGLE_SIZE) -> None:
        self.shingle_size = shingle_size

    def generate(
        self,
        document_id: str,
        source_uri: str,
        file_name: str,
        tokens: list[str],
        partition_id: int = 0,
        partition_count: int = 1,
    ) -> list[ShingleRecord]:
        """Slide a window of shingle_size tokens over the token list.

        Args:
            document_id: SHA-256 identifier for the source document.
            source_uri: Absolute path or URI of the source document.
            file_name: Original file name with extension.
            tokens: Normalized token list.
            partition_id: Zero-based index of this partition.
            partition_count: Total number of partitions.

        Returns:
            List of ShingleRecord with shingle_text, token_start, token_end,
            char_start, char_end set.  shingle_hash64 and shingle_hash_sha256
            are set to sentinel values (0 / '') until ShingleHashProcessor runs.
        """
        records: list[ShingleRecord] = []
        created_at = datetime.now(timezone.utc).isoformat()

        # Pre-compute cumulative char offsets for the token list
        offsets: list[int] = []
        pos = 0
        for tok in tokens:
            offsets.append(pos)
            pos += len(tok) + 1  # +1 for the space separator

        n = len(tokens)
        for i in range(max(0, n - self.shingle_size + 1)):
            window = tokens[i : i + self.shingle_size]
            shingle_text = " ".join(window)
            char_start = offsets[i]
            last = min(i + self.shingle_size - 1, n - 1)
            char_end = offsets[last] + len(tokens[last])

            records.append(
                ShingleRecord(
                    document_id=document_id,
                    partition_id=partition_id,
                    partition_count=partition_count,
                    source_uri=source_uri,
                    file_name=file_name,
                    page_no=0,
                    section_id=0,
                    shingle_id=i,
                    shingle_text=shingle_text,
                    shingle_hash64=0,
                    shingle_hash_sha256="",
                    token_start=i,
                    token_end=i + len(window) - 1,
                    char_start=char_start,
                    char_end=char_end,
                    normalization_version=NORMALIZATION_VERSION,
                    created_at_utc=created_at,
                )
            )

        log.info(
            "shingles_generated",
            document_id=document_id,
            shingle_count=len(records),
            shingle_size=self.shingle_size,
            partition_id=partition_id,
        )
        return records
