"""
File Name: document_partition_processor.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: DocumentPartitionProcessor — splits a token list into equal-size
             partitions for distributed processing (FR-025, ADR-011).

Requirements:
- Python 3.12+
"""

from __future__ import annotations

import logging
import math
import os
from datetime import datetime

import structlog

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

DEFAULT_PARTITION_SIZE = 50_000  # tokens per partition


class DocumentPartitionProcessor:
    """Split a normalized token list into fixed-size partitions.

    Args:
        partition_size: Max tokens per partition. Default 50 000.

    Returns:
        List of (partition_id, tokens_slice) tuples.
    """

    def __init__(self, partition_size: int = DEFAULT_PARTITION_SIZE) -> None:
        self.partition_size = partition_size

    def partition(self, tokens: list[str], document_id: str) -> list[tuple[int, list[str]]]:
        """Split tokens into consecutive non-overlapping partitions.

        Args:
            tokens: Full normalized token list for the document.
            document_id: SHA-256 document ID (used for logging).

        Returns:
            List of (partition_id, token_slice) in order.
            Returns [(0, tokens)] for documents fitting in one partition.
        """
        n = len(tokens)
        partition_count = max(1, math.ceil(n / self.partition_size))
        partitions = []
        for i in range(partition_count):
            start = i * self.partition_size
            end = min(start + self.partition_size, n)
            partitions.append((i, tokens[start:end]))
        log.info(
            "document_partitioned",
            document_id=document_id,
            token_count=n,
            partition_count=partition_count,
        )
        return partitions
