"""
File Name: tika_extractor.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: TikaDocumentTextExtractor — Apache Tika implementation of
             DocumentTextExtractor.  POC default extractor (FR-007, ADR-002).

Note: Requires the 'tika' Python package and a reachable Tika server.
      The tika package auto-starts a local JVM server on first use if
      TIKA_SERVER_JAR is not set.

Requirements:
- tika>=2.6
- Python 3.12+
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import structlog
from tika import parser as tika_parser

from docfp.interfaces.document_text_extractor import DocumentTextExtractor
from docfp.models.extracted_text import ExtractedDocumentText

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

EXTRACTION_ENGINE = "apache-tika"


class TikaDocumentTextExtractor(DocumentTextExtractor):
    """Extract text from documents using Apache Tika (POC default).

    Args:
        source_uri: Absolute file path of the document to extract text from.

    Returns:
        ExtractedDocumentText with full body text and Tika metadata.
    """

    def extract(self, source_uri: str) -> ExtractedDocumentText:
        """Run Tika parser on the source document and return extracted text.

        Args:
            source_uri: Absolute path or URI of the document.

        Returns:
            ExtractedDocumentText with text body, Tika metadata dict, and
            ocr_applied=False.
        """
        log.info("tika_extraction_start", source_uri=source_uri)

        parsed = tika_parser.from_file(source_uri)
        text: str = parsed.get("content") or ""
        metadata: dict = parsed.get("metadata") or {}

        log.info(
            "tika_extraction_complete",
            source_uri=source_uri,
            text_length=len(text),
            metadata_keys=list(metadata.keys()),
        )

        return ExtractedDocumentText(
            document_id="",  # populated by checksum processor downstream
            source_uri=source_uri,
            text=text.strip(),
            metadata=metadata,
            pages=[],
            extraction_engine=EXTRACTION_ENGINE,
            ocr_applied=False,
        )
