"""
File Name: checksum_processor.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: DocumentChecksumProcessor — computes a stable SHA-256 document_id
             from raw file bytes and stamps it onto an existing DocumentMetadata.

Requirements:
- Python 3.12+
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime

import structlog

from docfp.models.document_metadata import DocumentMetadata

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

READ_CHUNK = 65536  # 64 KB


class DocumentChecksumProcessor:
    """Compute and assign a stable SHA-256 document_id.

    Args:
        source_uri: Absolute path to the source document file.
        metadata: DocumentMetadata instance to stamp the document_id onto.

    Returns:
        The same DocumentMetadata instance with document_id set.
    """

    def compute_and_stamp(self, source_uri: str, metadata: DocumentMetadata) -> DocumentMetadata:
        """Read file bytes, compute SHA-256, and set metadata.document_id.

        Args:
            source_uri: Absolute path to the document file.
            metadata: DocumentMetadata whose document_id field will be filled.

        Returns:
            Updated DocumentMetadata with document_id = hex SHA-256 digest.
        """
        sha = hashlib.sha256()
        with open(source_uri, "rb") as fh:
            while chunk := fh.read(READ_CHUNK):
                sha.update(chunk)
        document_id = sha.hexdigest()
        metadata.document_id = document_id
        log.info("checksum_computed", file_name=metadata.file_name, document_id=document_id)
        return metadata
