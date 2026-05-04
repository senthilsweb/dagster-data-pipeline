## Tasks

### 1. Project scaffold
- [ ] 1.1 Create `document-fingerprint-pipeline/` directory with `pyproject.toml`, `dagster.yaml`, `workspace.yaml`, `README.md`
- [ ] 1.2 Create `src/docfp/__init__.py` and full package directory tree (models, interfaces, extractors, processors, writers, dagster_defs)

### 2. Models
- [ ] 2.1 Implement `models/document_metadata.py` — dataclass for metadata JSON schema (BRD §10)
- [ ] 2.2 Implement `models/extracted_text.py` — `ExtractedDocumentText` dataclass
- [ ] 2.3 Implement `models/normalized_text.py` — dataclass for normalized text output
- [ ] 2.4 Implement `models/shingle_record.py` — dataclass for Parquet row schema (BRD §11)

### 3. Interfaces
- [ ] 3.1 Implement `interfaces/document_text_extractor.py` — `DocumentTextExtractor` ABC
- [ ] 3.2 Implement `interfaces/ocr_processor.py` — `OcrProcessor` ABC
- [ ] 3.3 Implement `interfaces/normalizer.py` — `Normalizer` ABC
- [ ] 3.4 Implement `interfaces/shingle_generator.py` — `ShingleGenerator` ABC
- [ ] 3.5 Implement `interfaces/shingle_hasher.py` — `ShingleHasher` ABC
- [ ] 3.6 Implement `interfaces/artifact_writer.py` — `ArtifactWriter` ABC

### 4. Extractors
- [ ] 4.1 Implement `extractors/tika_extractor.py` — `TikaDocumentTextExtractor` (POC default)
- [ ] 4.2 Stub `extractors/docling_extractor.py` — `DoclingDocumentTextExtractor` (future)
- [ ] 4.3 Stub `extractors/markitdown_extractor.py` — `MarkItDownDocumentTextExtractor` (future)

### 5. Processors
- [ ] 5.1 Implement `processors/metadata_extractor.py` — `DocumentMetadataExtractor`
- [ ] 5.2 Implement `processors/checksum_processor.py` — `DocumentChecksumProcessor` (SHA-256)
- [ ] 5.3 Implement `processors/ocr_decision_processor.py` — `OcrDecisionProcessor`
- [ ] 5.4 Implement `processors/text_normalizer.py` — `TextNormalizer` (lowercase, unicode, whitespace, punctuation)
- [ ] 5.5 Implement `processors/tokenizer.py` — `TokenizerProcessor`
- [ ] 5.6 Implement `processors/word_shingle_generator.py` — `WordShingleGenerator` (sliding window, default size=5)
- [ ] 5.7 Implement `processors/shingle_hash_processor.py` — `ShingleHashProcessor` (SHA-256 + xxhash64)
- [ ] 5.8 Implement `processors/minhash_signature_builder.py` — `MinHashSignatureBuilder` (datasketch)
- [ ] 5.9 Implement `processors/lsh_index_builder.py` — `LshIndexBuilder` (datasketch)
- [ ] 5.10 Implement `processors/document_partition_processor.py` — `DocumentPartitionProcessor`
- [ ] 5.11 Implement `processors/partition_signature_merger.py` — `PartitionSignatureMerger`
- [ ] 5.12 Implement `processors/shingle_retention_processor.py` — `ShingleRetentionProcessor` (DLP-safe delete)

### 6. Writers
- [ ] 6.1 Implement `writers/metadata_json_writer.py` — `MetadataJsonWriter` → `{doc}.metadata.json`
- [ ] 6.2 Implement `writers/text_writer.py` — `RawTextWriter` + `NormalizedTextWriter`
- [ ] 6.3 Implement `writers/shingle_parquet_writer.py` — `ShingleParquetWriter` (PyArrow)
- [ ] 6.4 Implement `writers/document_signature_writer.py` — `DocumentSignatureWriter` → `{doc}.hash_signature.json`, `{doc}.minhash.json`

### 7. Dagster definitions
- [ ] 7.1 Implement `dagster_defs/resources.py` — extractor, normalizer, and hasher resources
- [ ] 7.2 Implement `dagster_defs/assets.py` — all 12 assets from BRD §8.1 with materialization metadata
- [ ] 7.3 Implement `dagster_defs/jobs.py` — full pipeline job definition
- [ ] 7.4 Implement `dagster_defs/schedules.py` — optional schedule definition

### 8. OCR integration
- [ ] 8.1 Implement `processors/ocr_decision_processor.py` routing logic (length threshold + config flag)
- [ ] 8.2 Wire `OcrProcessor` using `ocrmypdf` with Tesseract backend

### 9. Output folder structure
- [ ] 9.1 Create output folder layout: `output/{metadata,text,normalized,shingles,signatures,indexes,partitions}`
- [ ] 9.2 Validate file naming convention matches BRD §9 for all writer outputs

### 10. Testing
- [ ] 10.1 Unit test `TextNormalizer` — determinism, lowercase, whitespace
- [ ] 10.2 Unit test `WordShingleGenerator` — sliding window, edge cases (short text)
- [ ] 10.3 Unit test `ShingleHashProcessor` — SHA-256 and xxhash64 reproducibility
- [ ] 10.4 Unit test `DocumentChecksumProcessor` — stable document_id across runs
- [ ] 10.5 Integration test full pipeline with `data/input/` synthetic corpus (100 files from `articles_100.train`)
- [ ] 10.6 Validate DLP-safe shingle cleanup — confirm Parquet deleted after signature generation

### 11. POC execution validation (Success Criteria)
- [ ] 11.1 SC-001: Pipeline processes PDF, DOCX, PPTX, and TXT files
- [ ] 11.2 SC-002: One metadata JSON generated per document
- [ ] 11.3 SC-003: One shingle Parquet generated per document
- [ ] 11.4 SC-004: Failed steps rerun via Dagster without full pipeline restart
- [ ] 11.5 SC-005: Text extractor swapped without changing downstream processors
- [ ] 11.6 SC-006: Shingle output contains stable document_id and shingle hashes
- [ ] 11.7 SC-007: Normalization and shingling are deterministic and testable
- [ ] 11.8 SC-008: POC avoids vector embedding dependency
- [ ] 11.9 SC-009: POC produces retained MinHash signatures and LSH index
- [ ] 11.10 SC-010: Raw shingle artifacts deleted/expired after signature generation
- [ ] 11.11 SC-011: POC design supports document partitioning and final merge
