"""
File Name: shingle_retention_processor.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: ShingleRetentionProcessor — deletes the temporary shingle Parquet
             file after signature generation in DLP-safe mode (FR-022, ADR-012).

Requirements:
- Python 3.12+
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

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


class ShingleRetentionProcessor:
    """Handle post-signing lifecycle of the temporary shingle Parquet file.

    Args:
        dlp_safe_mode: When True, deletes the Parquet after signing.
                       When False (debug mode), retains it.

    Returns:
        True if the file was deleted, False if it was retained or not found.
    """

    def __init__(self, dlp_safe_mode: bool = True) -> None:
        self.dlp_safe_mode = dlp_safe_mode

    def process(self, parquet_path: Path, document_id: str) -> bool:
        """Delete or retain the shingle Parquet file.

        Args:
            parquet_path: Path to the {doc}_shingle.parquet file.
            document_id: SHA-256 document identifier (for logging).

        Returns:
            True if the file was deleted, False otherwise.
        """
        if not parquet_path.exists():
            log.info("shingle_retention_skip", document_id=document_id, reason="file_not_found")
            return False

        if self.dlp_safe_mode:
            parquet_path.unlink()
            log.info(
                "shingle_retention_deleted",
                document_id=document_id,
                path=str(parquet_path),
            )
            return True

        log.info(
            "shingle_retention_retained",
            document_id=document_id,
            path=str(parquet_path),
            reason="debug_mode",
        )
        return False
