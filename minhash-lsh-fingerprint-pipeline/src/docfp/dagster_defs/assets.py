"""
File Name: assets.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: Dagster asset definitions for the document fingerprinting pipeline.
             Each stage is an independently materializable asset (FR-016, ADR-001).
             All 12 BRD §8.1 assets are defined here.

Note: Assets operate on a single document at a time.  Batch runs are handled
      by iterating over the input folder outside Dagster or via a sensor.

Requirements:
- dagster>=1.9
- Python 3.12+
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import structlog
from dagster import AssetIn, Config, MetadataValue, Output, asset

from docfp.dagster_defs.resources import (
    ShingleHasherResource,
    TextExtractorResource,
    TextNormalizerResource,
)
from docfp.models.document_metadata import DocumentMetadata
from docfp.models.extracted_text import ExtractedDocumentText
from docfp.models.normalized_text import NormalizedText
from docfp.models.shingle_record import ShingleRecord
from docfp.processors.checksum_processor import DocumentChecksumProcessor
from docfp.processors.lsh_index_builder import LshIndexBuilder
from docfp.processors.metadata_extractor import DocumentMetadataExtractor
from docfp.processors.minhash_signature_builder import MinHashSignatureBuilder
from docfp.processors.ocr_decision_processor import OcrDecisionProcessor
from docfp.processors.partition_signature_merger import PartitionSignatureMerger
from docfp.processors.shingle_retention_processor import ShingleRetentionProcessor
from docfp.processors.tokenizer import TokenizerProcessor
from docfp.processors.word_shingle_generator import WordShingleGenerator
from docfp.writers.document_signature_writer import DocumentSignatureWriter
from docfp.writers.metadata_json_writer import MetadataJsonWriter
from docfp.writers.shingle_parquet_writer import ShingleParquetWriter
from docfp.writers.text_writer import NormalizedTextWriter, RawTextWriter

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


# ---------------------------------------------------------------------------
# Pipeline configuration
# ---------------------------------------------------------------------------


class PipelineConfig(Config):
    """Per-run configuration for the fingerprinting pipeline.

    Args:
        source_uri: Absolute path to the input document.
        output_root: Root output directory (sub-folders created automatically).
        shingle_size: Word-shingle window size. Default 5.
        minhash_num_perm: MinHash permutation count. Default 128.
        lsh_threshold: Jaccard similarity threshold for LSH. Default 0.5.
        dlp_safe_mode: When True deletes shingle Parquet after signing.
        ocr_enabled: Force OCR regardless of extracted text length.
        ocr_min_text_length: Trigger OCR when extracted text is shorter than this.
        pipeline_run_id: Optional run ID for traceability.
    """

    source_uri: str
    output_root: str = "output"
    shingle_size: int = 5
    minhash_num_perm: int = 128
    lsh_threshold: float = 0.5
    dlp_safe_mode: bool = True
    ocr_enabled: bool = False
    ocr_min_text_length: int = 50
    pipeline_run_id: str = ""


# ---------------------------------------------------------------------------
# Asset 1 — source_document
# ---------------------------------------------------------------------------


@asset
def source_document(config: PipelineConfig) -> dict:
    """Validate that the source document exists and return its path metadata.

    Args:
        config: PipelineConfig with source_uri and output_root.

    Returns:
        Dict with source_uri and file_name for downstream assets.
    """
    path = Path(config.source_uri)
    if not path.exists():
        raise FileNotFoundError(f"Source document not found: {config.source_uri}")
    log.info("source_document_ok", source_uri=config.source_uri)
    return {"source_uri": config.source_uri, "file_name": path.name}


# ---------------------------------------------------------------------------
# Asset 2 — document_metadata_json
# ---------------------------------------------------------------------------


@asset
def document_metadata_json(
    source_document: dict,
    config: PipelineConfig,
) -> dict:
    """Extract file metadata, compute document_id, and write metadata JSON.

    Args:
        source_document: Output of source_document asset.
        config: Pipeline configuration.

    Returns:
        Dict with document_id, file_name, source_uri, and metadata_json_path.
    """
    source_uri = source_document["source_uri"]
    out_dir = Path(config.output_root) / "metadata"

    meta: DocumentMetadata = DocumentMetadataExtractor().extract(
        source_uri, pipeline_run_id=config.pipeline_run_id or None
    )
    meta = DocumentChecksumProcessor().compute_and_stamp(source_uri, meta)
    json_path = MetadataJsonWriter().write(meta, out_dir)

    log.info("document_metadata_json_materialized", document_id=meta.document_id)
    return {
        "document_id": meta.document_id,
        "file_name": meta.file_name,
        "source_uri": source_uri,
        "metadata_json_path": str(json_path),
        "mime_type": meta.mime_type,
    }


# ---------------------------------------------------------------------------
# Asset 3 — raw_extracted_text
# ---------------------------------------------------------------------------


@asset
def raw_extracted_text(
    document_metadata_json: dict,
    config: PipelineConfig,
    extractor: TextExtractorResource,
) -> dict:
    """Extract raw text from the source document via the configured extractor.

    Args:
        document_metadata_json: Output of document_metadata_json asset.
        config: Pipeline configuration.
        extractor: TextExtractorResource providing the active extractor engine.

    Returns:
        Dict with document_id, source_uri, text, extraction_engine, and
        extracted_text_path.
    """
    source_uri = document_metadata_json["source_uri"]
    document_id = document_metadata_json["document_id"]
    out_dir = Path(config.output_root) / "text"

    result: ExtractedDocumentText = extractor.get_extractor().extract(source_uri)
    result.document_id = document_id

    text_path = RawTextWriter().write(result, out_dir)

    log.info(
        "raw_extracted_text_materialized",
        document_id=document_id,
        text_length=len(result.text),
    )
    return {
        "document_id": document_id,
        "source_uri": source_uri,
        "file_name": document_metadata_json["file_name"],
        "text": result.text,
        "extraction_engine": result.extraction_engine,
        "ocr_applied": result.ocr_applied,
        "extracted_text_path": str(text_path),
    }


# ---------------------------------------------------------------------------
# Asset 4 — ocr_extracted_text
# ---------------------------------------------------------------------------


@asset
def ocr_extracted_text(
    raw_extracted_text: dict,
    config: PipelineConfig,
) -> dict:
    """Apply OCR if required; otherwise pass raw text through unchanged.

    Args:
        raw_extracted_text: Output of raw_extracted_text asset.
        config: Pipeline configuration.

    Returns:
        Dict with text and ocr_applied flag (may be same as raw_extracted_text).
    """
    decision = OcrDecisionProcessor(
        min_text_length=config.ocr_min_text_length,
        ocr_enabled=config.ocr_enabled,
    )
    needs_ocr = decision.should_run_ocr(
        raw_extracted_text["text"], raw_extracted_text["source_uri"]
    )

    if needs_ocr:
        log.info(
            "ocr_required",
            document_id=raw_extracted_text["document_id"],
            reason="text_too_short_or_forced",
        )
        # OCRmyPDF wired in Task 8 — stub raises NotImplementedError for now
        raise NotImplementedError(
            "OCR path not yet wired. Install OcrProcessor (Task 8)."
        )

    log.info(
        "ocr_skipped",
        document_id=raw_extracted_text["document_id"],
    )
    return {**raw_extracted_text, "ocr_applied": False}


# ---------------------------------------------------------------------------
# Asset 5 — normalized_text
# ---------------------------------------------------------------------------


@asset
def normalized_text(
    ocr_extracted_text: dict,
    config: PipelineConfig,
    normalizer: TextNormalizerResource,
) -> dict:
    """Normalize extracted text deterministically.

    Args:
        ocr_extracted_text: Output of ocr_extracted_text asset.
        config: Pipeline configuration.
        normalizer: TextNormalizerResource providing the active normalizer.

    Returns:
        Dict with normalized text, token_count, and normalized_text_path.
    """
    document_id = ocr_extracted_text["document_id"]
    out_dir = Path(config.output_root) / "normalized"

    result: NormalizedText = normalizer.get_normalizer().normalize(
        document_id=document_id,
        source_uri=ocr_extracted_text["source_uri"],
        text=ocr_extracted_text["text"],
    )
    norm_path = NormalizedTextWriter().write(result, out_dir)

    log.info(
        "normalized_text_materialized",
        document_id=document_id,
        token_count=result.token_count,
    )
    return {
        "document_id": document_id,
        "source_uri": ocr_extracted_text["source_uri"],
        "file_name": ocr_extracted_text["file_name"],
        "normalized_text": result.text,
        "token_count": result.token_count,
        "normalization_version": result.normalization_version,
        "normalized_text_path": str(norm_path),
    }


# ---------------------------------------------------------------------------
# Asset 6 — document_shingles
# ---------------------------------------------------------------------------


@asset
def document_shingles(
    normalized_text: dict,
    config: PipelineConfig,
) -> dict:
    """Generate word shingles from normalized text.

    Args:
        normalized_text: Output of normalized_text asset.
        config: Pipeline configuration.

    Returns:
        Dict with shingle list and count metadata.
    """
    document_id = normalized_text["document_id"]
    tokens = TokenizerProcessor().tokenize(normalized_text["normalized_text"], document_id)

    records: list[ShingleRecord] = WordShingleGenerator(
        shingle_size=config.shingle_size
    ).generate(
        document_id=document_id,
        source_uri=normalized_text["source_uri"],
        file_name=normalized_text["file_name"],
        tokens=tokens,
    )

    log.info(
        "document_shingles_materialized",
        document_id=document_id,
        shingle_count=len(records),
    )
    return {
        "document_id": document_id,
        "file_name": normalized_text["file_name"],
        "source_uri": normalized_text["source_uri"],
        "shingles": records,
        "shingle_count": len(records),
        "normalization_version": normalized_text["normalization_version"],
    }


# ---------------------------------------------------------------------------
# Asset 7 — document_shingle_hashes
# ---------------------------------------------------------------------------


@asset
def document_shingle_hashes(
    document_shingles: dict,
    hasher: ShingleHasherResource,
) -> dict:
    """Compute SHA-256 and xxhash64 for every shingle.

    Args:
        document_shingles: Output of document_shingles asset.
        hasher: ShingleHasherResource providing the active hasher.

    Returns:
        Dict with hashed shingle records.
    """
    records: list[ShingleRecord] = document_shingles["shingles"]
    hashed = hasher.get_hasher().hash_records(records)

    log.info(
        "document_shingle_hashes_materialized",
        document_id=document_shingles["document_id"],
        shingle_count=len(hashed),
    )
    return {**document_shingles, "shingles": hashed}


# ---------------------------------------------------------------------------
# Asset 8 — document_shingle_parquet
# ---------------------------------------------------------------------------


@asset
def document_shingle_parquet(
    document_shingle_hashes: dict,
    config: PipelineConfig,
) -> dict:
    """Write shingle records to a temporary Parquet file.

    Args:
        document_shingle_hashes: Output of document_shingle_hashes asset.
        config: Pipeline configuration.

    Returns:
        Dict with parquet_path and row_count.
    """
    out_dir = Path(config.output_root) / "shingles"
    parquet_path = ShingleParquetWriter().write(
        document_shingle_hashes["shingles"], out_dir
    )

    log.info(
        "document_shingle_parquet_materialized",
        document_id=document_shingle_hashes["document_id"],
        parquet_path=str(parquet_path),
        row_count=len(document_shingle_hashes["shingles"]),
    )
    return {
        "document_id": document_shingle_hashes["document_id"],
        "file_name": document_shingle_hashes["file_name"],
        "source_uri": document_shingle_hashes["source_uri"],
        "shingles": document_shingle_hashes["shingles"],
        "parquet_path": str(parquet_path),
        "row_count": len(document_shingle_hashes["shingles"]),
    }


# ---------------------------------------------------------------------------
# Asset 9 — document_hash_signature
# ---------------------------------------------------------------------------


@asset
def document_hash_signature(
    document_shingle_parquet: dict,
    config: PipelineConfig,
) -> dict:
    """Build and write the document-level SHA-256 hash signature.

    Args:
        document_shingle_parquet: Output of document_shingle_parquet asset.
        config: Pipeline configuration.

    Returns:
        Dict with hash_signature_sha256, unique_shingle_hash_count, and
        sig_path.
    """
    import hashlib

    shingles: list[ShingleRecord] = document_shingle_parquet["shingles"]
    document_id = document_shingle_parquet["document_id"]

    unique_hashes = sorted({r.shingle_hash_sha256 for r in shingles})
    combined = "".join(unique_hashes).encode("utf-8")
    sig_sha256 = hashlib.sha256(combined).hexdigest()

    log.info(
        "document_hash_signature_computed",
        document_id=document_id,
        unique_hash_count=len(unique_hashes),
    )
    return {
        "document_id": document_id,
        "file_name": document_shingle_parquet["file_name"],
        "source_uri": document_shingle_parquet["source_uri"],
        "shingles": shingles,
        "parquet_path": document_shingle_parquet["parquet_path"],
        "hash_signature_sha256": sig_sha256,
        "unique_shingle_hash_count": len(unique_hashes),
        "total_shingle_count": len(shingles),
    }


# ---------------------------------------------------------------------------
# Asset 10 — document_minhash_signature
# ---------------------------------------------------------------------------


@asset
def document_minhash_signature(
    document_hash_signature: dict,
    config: PipelineConfig,
) -> dict:
    """Build MinHash signature and write both signature JSON artifacts.

    Args:
        document_hash_signature: Output of document_hash_signature asset.
        config: Pipeline configuration.

    Returns:
        Dict with sig_path, minhash_path, and minhash object.
    """
    shingles: list[ShingleRecord] = document_hash_signature["shingles"]
    document_id = document_hash_signature["document_id"]
    out_dir = Path(config.output_root) / "signatures"

    hashes64 = [r.shingle_hash64 for r in shingles]
    mh = MinHashSignatureBuilder(num_perm=config.minhash_num_perm).build(hashes64, document_id)

    sig_path, minhash_path = DocumentSignatureWriter().write(
        document_id=document_id,
        source_uri=document_hash_signature["source_uri"],
        file_name=document_hash_signature["file_name"],
        signature_version="v1",
        shingle_size=config.shingle_size,
        total_shingle_count=document_hash_signature["total_shingle_count"],
        unique_shingle_hash_count=document_hash_signature["unique_shingle_hash_count"],
        hash_signature_sha256=document_hash_signature["hash_signature_sha256"],
        minhash=mh,
        lsh_bucket_keys=[],
        partition_merge_status="single-partition",
        output_dir=out_dir,
    )

    # DLP-safe shingle Parquet cleanup
    ShingleRetentionProcessor(dlp_safe_mode=config.dlp_safe_mode).process(
        Path(document_hash_signature["parquet_path"]),
        document_id,
    )

    log.info(
        "document_minhash_signature_materialized",
        document_id=document_id,
        sig_path=str(sig_path),
    )
    return {
        "document_id": document_id,
        "file_name": document_hash_signature["file_name"],
        "minhash": mh,
        "sig_path": str(sig_path),
        "minhash_path": str(minhash_path),
        "hash_signature_sha256": document_hash_signature["hash_signature_sha256"],
    }


# ---------------------------------------------------------------------------
# Asset 11 — lsh_index
# ---------------------------------------------------------------------------


@asset
def lsh_index(
    document_minhash_signature: dict,
    config: PipelineConfig,
) -> dict:
    """Insert the document MinHash into the corpus LSH index.

    Args:
        document_minhash_signature: Output of document_minhash_signature asset.
        config: Pipeline configuration.

    Returns:
        Dict with lsh_index_path.
    """
    out_dir = Path(config.output_root) / "indexes"
    document_id = document_minhash_signature["document_id"]
    mh = document_minhash_signature["minhash"]

    lsh_b = LshIndexBuilder(
        threshold=config.lsh_threshold, num_perm=config.minhash_num_perm
    )
    lsh = lsh_b.build({document_id: mh})
    idx_path = lsh_b.save(lsh, out_dir)

    log.info("lsh_index_materialized", document_id=document_id, index_path=str(idx_path))
    return {
        "document_id": document_id,
        "lsh_index_path": str(idx_path),
    }


# ---------------------------------------------------------------------------
# Asset 12 — document_fingerprint_summary
# ---------------------------------------------------------------------------


@asset
def document_fingerprint_summary(
    document_minhash_signature: dict,
    lsh_index: dict,
    config: PipelineConfig,
) -> dict:
    """Write a summary JSON combining all pipeline outputs.

    Args:
        document_minhash_signature: Output of document_minhash_signature asset.
        lsh_index: Output of lsh_index asset.
        config: Pipeline configuration.

    Returns:
        Dict with summary_path.
    """
    import json

    document_id = document_minhash_signature["document_id"]
    out_dir = Path(config.output_root) / "signatures"
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = Path(document_minhash_signature["file_name"]).stem
    summary = {
        "document_id": document_id,
        "file_name": document_minhash_signature["file_name"],
        "hash_signature_sha256": document_minhash_signature["hash_signature_sha256"],
        "sig_path": document_minhash_signature["sig_path"],
        "minhash_path": document_minhash_signature["minhash_path"],
        "lsh_index_path": lsh_index["lsh_index_path"],
        "pipeline_run_id": config.pipeline_run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    summary_path = out_dir / f"{stem}.fingerprint_summary.json"
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    log.info(
        "document_fingerprint_summary_materialized",
        document_id=document_id,
        summary_path=str(summary_path),
    )
    return {"document_id": document_id, "summary_path": str(summary_path)}
