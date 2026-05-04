"""
File Name: __init__.py (dagster_defs)
Author: Senthilnathan Karuppaiah
Date: 2026-05-03
Description: Dagster Definitions entry point — exposes all assets, jobs, and
             resources for the document fingerprinting pipeline.

Requirements:
- dagster>=1.9
"""

from __future__ import annotations

from dagster import Definitions

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
from docfp.dagster_defs.jobs import fingerprint_pipeline_job
from docfp.dagster_defs.resources import (
    ShingleHasherResource,
    TextExtractorResource,
    TextNormalizerResource,
)
from docfp.dagster_defs.schedules import schedules

defs = Definitions(
    assets=[
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
    jobs=[fingerprint_pipeline_job],
    resources={
        "extractor": TextExtractorResource(),
        "normalizer": TextNormalizerResource(),
        "hasher": ShingleHasherResource(),
    },
    schedules=schedules,
)
