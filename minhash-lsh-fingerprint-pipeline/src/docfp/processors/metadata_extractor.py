"""
File Name: metadata_extractor.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: DocumentMetadataExtractor — extracts file-level metadata (MIME type,
             size, extension) using python-magic and pathlib.

Requirements:
- python-magic>=0.4
- Python 3.12+
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import magic
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


class DocumentMetadataExtractor:
    """Extract file-level metadata for a document.

    Args:
        source_uri: Absolute path to the document file.
        pipeline_run_id: Optional Dagster run ID for traceability.

    Returns:
        DocumentMetadata with MIME type, size, and extension populated.
        document_id is left empty — filled by DocumentChecksumProcessor.
    """

    def extract(self, source_uri: str, pipeline_run_id: str | None = None) -> DocumentMetadata:
        """Read file metadata and return a DocumentMetadata instance.

        Args:
            source_uri: Absolute path to the document file.
            pipeline_run_id: Optional Dagster pipeline run identifier.

        Returns:
            DocumentMetadata with all file attributes populated.
            document_id is an empty string at this stage.
        """
        path = Path(source_uri)
        file_size = path.stat().st_size
        mime_type = magic.from_file(str(path), mime=True)
        created_at = datetime.now(timezone.utc).isoformat()

        log.info(
            "metadata_extracted",
            file_name=path.name,
            mime_type=mime_type,
            file_size_bytes=file_size,
        )

        return DocumentMetadata(
            document_id="",
            source_uri=source_uri,
            file_name=path.name,
            file_size_bytes=file_size,
            mime_type=mime_type,
            extension=path.suffix.lower(),
            created_at_utc=created_at,
            pipeline_run_id=pipeline_run_id,
        )
