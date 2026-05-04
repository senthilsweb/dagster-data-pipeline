"""
File Name: lsh_index_builder.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: LshIndexBuilder — builds and queries a datasketch MinHashLSH index
             for approximate near-duplicate detection (FR-024, ADR-010).

Requirements:
- datasketch>=1.6
- Python 3.12+
"""

from __future__ import annotations

import logging
import os
import pickle
from datetime import datetime
from pathlib import Path

import structlog
from datasketch import MinHash, MinHashLSH

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

DEFAULT_THRESHOLD = 0.5
DEFAULT_NUM_PERM = 128
LSH_INDEX_FILE = "corpus_lsh_index.pkl"


class LshIndexBuilder:
    """Build and persist a MinHash LSH index for the full document corpus.

    Args:
        threshold: Jaccard similarity threshold for LSH banding. Default 0.5.
        num_perm: MinHash permutation count (must match signature builder). Default 128.

    Returns:
        MinHashLSH instance loaded with all provided document signatures.
    """

    def __init__(
        self, threshold: float = DEFAULT_THRESHOLD, num_perm: int = DEFAULT_NUM_PERM
    ) -> None:
        self.threshold = threshold
        self.num_perm = num_perm

    def build(self, signatures: dict[str, MinHash]) -> MinHashLSH:
        """Insert all document MinHash signatures into an LSH index.

        Args:
            signatures: Mapping of document_id → MinHash signature.

        Returns:
            Populated MinHashLSH instance ready for querying.
        """
        lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
        for doc_id, mh in signatures.items():
            lsh.insert(doc_id, mh)
        log.info("lsh_index_built", document_count=len(signatures), threshold=self.threshold)
        return lsh

    def save(self, lsh: MinHashLSH, output_dir: Path) -> Path:
        """Persist the LSH index to disk as a pickle file.

        Args:
            lsh: The MinHashLSH index to persist.
            output_dir: Directory to write the index file.

        Returns:
            Path of the written pickle file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / LSH_INDEX_FILE
        with open(out_path, "wb") as fh:
            pickle.dump(lsh, fh)
        log.info("lsh_index_saved", path=str(out_path))
        return out_path

    def load(self, index_path: Path) -> MinHashLSH:
        """Load a previously persisted LSH index from disk.

        Args:
            index_path: Path to the pickle file.

        Returns:
            Deserialized MinHashLSH instance.
        """
        with open(index_path, "rb") as fh:
            lsh = pickle.load(fh)  # noqa: S301 — trusted internal artifact
        log.info("lsh_index_loaded", path=str(index_path))
        return lsh

    def query(self, lsh: MinHashLSH, query_mh: MinHash) -> list[str]:
        """Find candidate near-duplicate documents for a query signature.

        Args:
            lsh: Populated MinHashLSH index.
            query_mh: MinHash signature of the query document.

        Returns:
            List of document_id strings that are candidates.
        """
        return lsh.query(query_mh)
