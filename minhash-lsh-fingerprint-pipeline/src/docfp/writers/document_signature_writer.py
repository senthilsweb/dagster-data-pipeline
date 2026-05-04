"""
File Name: document_signature_writer.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: DocumentSignatureWriter — writes {doc}.hash_signature.json and
             {doc}.minhash.json (FR-021, FR-023, ADR-012).

Requirements:
- datasketch>=1.6
- Python 3.12+
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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


class DocumentSignatureWriter:
    """Write the retained document signature artifacts.

    Writes two files per document:
      - {doc}.hash_signature.json  (full BRD §11.1 schema)
      - {doc}.minhash.json         (MinHash signature values)

    Args:
        document_id: SHA-256 checksum of the source file.
        source_uri: Absolute path of the source document.
        file_name: Original file name.
        signature_version: Version string for the signature schema.
        shingle_size: Window size used during shingle generation.
        total_shingle_count: Total shingles generated (including duplicates).
        unique_shingle_hash_count: Distinct shingle hash count.
        hash_signature_sha256: Merged document-level SHA-256 hash signature.
        minhash: datasketch.MinHash instance.
        lsh_bucket_keys: List of LSH bucket identifiers.
        partition_merge_status: 'single-partition' or 'merged-partition'.
        output_dir: Directory to write both files.

    Returns:
        Tuple of (hash_signature_path, minhash_path).
    """

    def write(
        self,
        document_id: str,
        source_uri: str,
        file_name: str,
        signature_version: str,
        shingle_size: int,
        total_shingle_count: int,
        unique_shingle_hash_count: int,
        hash_signature_sha256: str,
        minhash: MinHash,
        lsh_bucket_keys: list[str],
        partition_merge_status: str,
        output_dir: Path,
    ) -> tuple[Path, Path]:
        """Serialize and write both signature artifacts.

        Args:
            document_id: SHA-256 document identifier.
            source_uri: Absolute source path.
            file_name: Original file name.
            signature_version: Signature schema version.
            shingle_size: Shingle window size.
            total_shingle_count: Total shingles generated.
            unique_shingle_hash_count: Unique shingle hash count.
            hash_signature_sha256: Document-level merged SHA-256.
            minhash: datasketch MinHash instance.
            lsh_bucket_keys: LSH bucket key strings.
            partition_merge_status: Merge status string.
            output_dir: Target directory (created if absent).

        Returns:
            Tuple of (hash_signature_path, minhash_path).
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(file_name).stem
        created_at = datetime.now(timezone.utc).isoformat()

        # --- hash_signature.json ---
        sig_doc: dict[str, Any] = {
            "document_id": document_id,
            "source_uri": source_uri,
            "file_name": file_name,
            "signature_version": signature_version,
            "shingle_size": shingle_size,
            "total_shingle_count": total_shingle_count,
            "unique_shingle_hash_count": unique_shingle_hash_count,
            "hash_signature_sha256": hash_signature_sha256,
            "minhash_signature": minhash.hashvalues.tolist(),
            "lsh_bucket_keys": lsh_bucket_keys,
            "partition_merge_status": partition_merge_status,
            "created_at_utc": created_at,
        }
        sig_path = output_dir / f"{stem}.hash_signature.json"
        with open(sig_path, "w", encoding="utf-8") as fh:
            json.dump(sig_doc, fh, indent=2)

        # --- minhash.json ---
        minhash_doc: dict[str, Any] = {
            "document_id": document_id,
            "file_name": file_name,
            "num_perm": int(minhash.hashvalues.shape[0]),
            "hashvalues": minhash.hashvalues.tolist(),
            "created_at_utc": created_at,
        }
        minhash_path = output_dir / f"{stem}.minhash.json"
        with open(minhash_path, "w", encoding="utf-8") as fh:
            json.dump(minhash_doc, fh, indent=2)

        log.info(
            "document_signature_written",
            document_id=document_id,
            sig_path=str(sig_path),
            minhash_path=str(minhash_path),
        )
        return sig_path, minhash_path
