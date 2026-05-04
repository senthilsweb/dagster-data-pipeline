"""
File Name: document_metadata.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: DocumentMetadata dataclass — persisted as {doc}.metadata.json.
             Covers BRD §10 retained metadata schema.

Requirements:
- Python 3.12+
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DocumentMetadata:
    """Full metadata record written to {doc}.metadata.json.

    Args:
        document_id: SHA-256 checksum of raw file bytes — stable unique ID.
        source_uri: Absolute path or URI of the source document.
        file_name: Original file name with extension.
        file_size_bytes: File size in bytes.
        mime_type: MIME type detected by python-magic.
        extension: Lower-case file extension (e.g. '.pdf').
        created_at_utc: ISO-8601 UTC timestamp of pipeline ingestion.
        text_extraction_engine: Name of the extractor used (e.g. 'apache-tika').
        ocr_applied: True when OCR was run on this document.
        normalization_version: Identifier of the normalization rule set applied.
        partition_count: Number of partitions the document was split into.
        pipeline_run_id: Dagster run ID for traceability.

    Returns:
        DocumentMetadata instance.
    """

    document_id: str
    source_uri: str
    file_name: str
    file_size_bytes: int
    mime_type: str
    extension: str
    created_at_utc: str
    text_extraction_engine: str = "apache-tika"
    ocr_applied: bool = False
    normalization_version: str = "v1"
    partition_count: int = 1
    pipeline_run_id: Optional[str] = None
    extra: dict = field(default_factory=dict)
