"""
File Name: jobs.py
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: Dagster job definitions for the document fingerprinting pipeline.

Requirements:
- dagster>=1.9
- Python 3.12+
"""

from __future__ import annotations

from dagster import define_asset_job

from docfp.dagster_defs.assets import (
    document_fingerprint_summary,
    document_hash_signature,
    document_metadata_json,
    document_minhash_signature,
    document_shingle_hashes,
    document_shingle_parquet,
    document_shingles,
    lsh_index,
    normalized_text,
    ocr_extracted_text,
    raw_extracted_text,
    source_document,
)

fingerprint_pipeline_job = define_asset_job(
    name="fingerprint_pipeline_job",
    selection=[
        source_document,
        document_metadata_json,
        raw_extracted_text,
        ocr_extracted_text,
        normalized_text,
        document_shingles,
        document_shingle_hashes,
        document_shingle_parquet,
        document_hash_signature,
        document_minhash_signature,
        lsh_index,
        document_fingerprint_summary,
    ],
    description="Full document fingerprinting pipeline: ingest → extract → normalize → shingle → sign → LSH",
)
