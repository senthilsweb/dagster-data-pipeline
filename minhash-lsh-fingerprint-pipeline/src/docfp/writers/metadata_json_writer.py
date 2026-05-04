"""
File Name: metadata_json_writer.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: MetadataJsonWriter — writes DocumentMetadata to {doc}.metadata.json
             in the output/metadata folder.

Requirements:
- Python 3.12+
"""

from __future__ import annotations

import dataclasses
import json
import logging
import os
from datetime import datetime
from pathlib import Path

import structlog

from docfp.interfaces.artifact_writer import ArtifactWriter
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


class MetadataJsonWriter(ArtifactWriter):
    """Write DocumentMetadata to a JSON file.

    Args:
        artifact: DocumentMetadata instance to serialise.
        output_dir: Destination directory (created if absent).

    Returns:
        Path of the written {doc}.metadata.json file.
    """

    def write(self, artifact: DocumentMetadata, output_dir: Path) -> Path:
        """Serialize DocumentMetadata to JSON and write to disk.

        Args:
            artifact: DocumentMetadata to write.
            output_dir: Target directory.

        Returns:
            Path of the written file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(artifact.file_name).stem
        out_path = output_dir / f"{stem}.metadata.json"
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(dataclasses.asdict(artifact), fh, indent=2)
        log.info("metadata_json_written", path=str(out_path), document_id=artifact.document_id)
        return out_path
