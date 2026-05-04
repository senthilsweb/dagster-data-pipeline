"""
File Name: shingle_parquet_writer.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: ShingleParquetWriter — writes a list of ShingleRecord objects to a
             temporary {doc}_shingle.parquet file using PyArrow (FR-014, ADR-006).

Requirements:
- pyarrow>=18
- Python 3.12+
"""

from __future__ import annotations

import dataclasses
import logging
import os
from datetime import datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import structlog

from docfp.interfaces.artifact_writer import ArtifactWriter
from docfp.models.shingle_record import ShingleRecord

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

SHINGLE_SCHEMA = pa.schema(
    [
        pa.field("document_id", pa.string()),
        pa.field("partition_id", pa.int32()),
        pa.field("partition_count", pa.int32()),
        pa.field("source_uri", pa.string()),
        pa.field("file_name", pa.string()),
        pa.field("page_no", pa.int32()),
        pa.field("section_id", pa.int32()),
        pa.field("shingle_id", pa.int64()),
        pa.field("shingle_text", pa.string()),
        pa.field("shingle_hash64", pa.int64()),
        pa.field("shingle_hash_sha256", pa.string()),
        pa.field("token_start", pa.int64()),
        pa.field("token_end", pa.int64()),
        pa.field("char_start", pa.int64()),
        pa.field("char_end", pa.int64()),
        pa.field("normalization_version", pa.string()),
        pa.field("created_at_utc", pa.string()),
    ]
)


class ShingleParquetWriter(ArtifactWriter):
    """Write ShingleRecord list to {doc}_shingle.parquet using PyArrow.

    Args:
        artifact: List of ShingleRecord objects.
        output_dir: Destination directory.

    Returns:
        Path of the written {doc}_shingle.parquet file.
    """

    def write(self, artifact: list[ShingleRecord], output_dir: Path) -> Path:
        """Convert ShingleRecord list to PyArrow table and write Parquet.

        Args:
            artifact: List of ShingleRecord instances.
            output_dir: Target directory (created if absent).

        Returns:
            Path of the written Parquet file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        if not artifact:
            raise ValueError("Cannot write an empty shingle list to Parquet.")

        rows = []
        for r in artifact:
            row = dataclasses.asdict(r)
            # xxhash.xxh64 returns unsigned uint64; PyArrow int64 is signed.
            # Reinterpret as signed so values >2^63-1 don't overflow.
            h = row["shingle_hash64"]
            if h >= (1 << 63):
                row["shingle_hash64"] = h - (1 << 64)
            rows.append(row)
        table = pa.Table.from_pylist(rows, schema=SHINGLE_SCHEMA)
        file_name = Path(artifact[0].file_name).stem
        out_path = output_dir / f"{file_name}_shingle.parquet"
        pq.write_table(table, str(out_path))
        log.info(
            "shingle_parquet_written",
            path=str(out_path),
            row_count=len(artifact),
            document_id=artifact[0].document_id,
        )
        return out_path
