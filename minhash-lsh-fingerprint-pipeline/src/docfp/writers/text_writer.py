"""
File Name: text_writer.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: RawTextWriter and NormalizedTextWriter — write extracted and
             normalized text to {doc}.extracted.txt and {doc}.normalized.txt.

Requirements:
- Python 3.12+
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

import structlog

from docfp.interfaces.artifact_writer import ArtifactWriter
from docfp.models.extracted_text import ExtractedDocumentText
from docfp.models.normalized_text import NormalizedText

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


class RawTextWriter(ArtifactWriter):
    """Write raw extracted text to {doc}.extracted.txt.

    Args:
        artifact: ExtractedDocumentText instance.
        output_dir: Destination directory.

    Returns:
        Path of the written {doc}.extracted.txt file.
    """

    def write(self, artifact: ExtractedDocumentText, output_dir: Path) -> Path:
        """Write extracted text body to disk.

        Args:
            artifact: ExtractedDocumentText to write.
            output_dir: Target directory (created if absent).

        Returns:
            Path of the written file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(artifact.source_uri).stem
        out_path = output_dir / f"{stem}.extracted.txt"
        out_path.write_text(artifact.text, encoding="utf-8")
        log.info("raw_text_written", path=str(out_path), document_id=artifact.document_id)
        return out_path


class NormalizedTextWriter(ArtifactWriter):
    """Write normalized text to {doc}.normalized.txt.

    Args:
        artifact: NormalizedText instance.
        output_dir: Destination directory.

    Returns:
        Path of the written {doc}.normalized.txt file.
    """

    def write(self, artifact: NormalizedText, output_dir: Path) -> Path:
        """Write normalized text body to disk.

        Args:
            artifact: NormalizedText to write.
            output_dir: Target directory (created if absent).

        Returns:
            Path of the written file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(artifact.source_uri).stem
        out_path = output_dir / f"{stem}.normalized.txt"
        out_path.write_text(artifact.text, encoding="utf-8")
        log.info("normalized_text_written", path=str(out_path), document_id=artifact.document_id)
        return out_path
