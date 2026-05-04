"""
File Name: partition_signature_merger.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: PartitionSignatureMerger — merges per-partition sorted unique shingle
             hash sets and MinHash states into a single document-level signature
             (FR-026, ADR-011).

Requirements:
- datasketch>=1.6
- Python 3.12+
"""

from __future__ import annotations

import hashlib
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


class PartitionSignatureMerger:
    """Merge per-partition shingle hash sets into a document-level signature.

    Args:
        partition_hash_sets: List of sets of shingle_hash_sha256 strings,
                             one set per partition.
        partition_minhashes: List of datasketch.MinHash objects, one per
                             partition.
        document_id: SHA-256 document identifier (for logging).

    Returns:
        Tuple of (merged_hash_signature_sha256, merged_minhash, partition_merge_status).
    """

    def merge(
        self,
        partition_hash_sets: list[set[str]],
        partition_minhashes: list[MinHash],
        document_id: str,
    ) -> tuple[str, MinHash, str]:
        """Merge partition-level artifacts into a single document signature.

        Args:
            partition_hash_sets: Per-partition sets of shingle SHA-256 hashes.
            partition_minhashes: Per-partition datasketch MinHash objects.
            document_id: SHA-256 document identifier.

        Returns:
            Tuple of:
              - merged_hash_signature_sha256: SHA-256 over sorted union of all hashes
              - merged_minhash: MinHash built from the combined unique hash set
              - partition_merge_status: 'single-partition' or 'merged-partition'
        """
        unified: set[str] = set()
        for hs in partition_hash_sets:
            unified.update(hs)

        sorted_hashes = sorted(unified)
        combined = "".join(sorted_hashes).encode("utf-8")
        merged_sig = hashlib.sha256(combined).hexdigest()

        # Rebuild a MinHash from the unified hash set
        from docfp.processors.minhash_signature_builder import MinHashSignatureBuilder  # noqa: PLC0415

        num_perm = partition_minhashes[0].hashvalues.shape[0] if partition_minhashes else 128
        builder = MinHashSignatureBuilder(num_perm=num_perm)
        import xxhash  # noqa: PLC0415

        merged_mh = builder.build(
            [xxhash.xxh64(h.encode("utf-8")).intdigest() for h in sorted_hashes],
            document_id=document_id,
        )

        status = "single-partition" if len(partition_hash_sets) <= 1 else "merged-partition"
        log.info(
            "partitions_merged",
            document_id=document_id,
            partition_count=len(partition_hash_sets),
            unique_hash_count=len(unified),
            merge_status=status,
        )
        return merged_sig, merged_mh, status
