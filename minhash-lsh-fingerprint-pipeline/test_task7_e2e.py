"""
End-to-end integration test — single document, full fingerprinting pipeline.
"""
import hashlib, json, shutil, sys
from pathlib import Path

INPUT_DOC = Path("/Users/krs/work/data-pipelines/dagster-data-pipeline/minhash-lsh-fingerprint-pipeline/data/input/azerbaijani_government_troops_t5207.md")
OUTPUT_ROOT = Path("/Users/krs/work/data-pipelines/dagster-data-pipeline/minhash-lsh-fingerprint-pipeline/data/output")
PIPELINE_RUN_ID = "e2e-smoke-test-001"
SHINGLE_SIZE = 5
MINHASH_NUM_PERM = 128
LSH_THRESHOLD = 0.5
DLP_SAFE_MODE = False  # retain shingles Parquet for debug inspection

# Wipe only the sub-folders we own so existing data/input is untouched
for sub in ("metadata", "text", "normalized", "shingles", "signatures", "indexes"):
    sub_dir = OUTPUT_ROOT / sub
    if sub_dir.exists():
        shutil.rmtree(sub_dir)
    sub_dir.mkdir(parents=True)

from docfp.models.document_metadata import DocumentMetadata
from docfp.processors.checksum_processor import DocumentChecksumProcessor
from docfp.processors.document_partition_processor import DocumentPartitionProcessor
from docfp.processors.lsh_index_builder import LshIndexBuilder
from docfp.processors.metadata_extractor import DocumentMetadataExtractor
from docfp.processors.minhash_signature_builder import MinHashSignatureBuilder
from docfp.processors.ocr_decision_processor import OcrDecisionProcessor
from docfp.processors.shingle_hash_processor import ShingleHashProcessor
from docfp.processors.shingle_retention_processor import ShingleRetentionProcessor
from docfp.processors.text_normalizer import TextNormalizer
from docfp.processors.tokenizer import TokenizerProcessor
from docfp.processors.word_shingle_generator import WordShingleGenerator
from docfp.writers.document_signature_writer import DocumentSignatureWriter
from docfp.writers.metadata_json_writer import MetadataJsonWriter
from docfp.writers.shingle_parquet_writer import ShingleParquetWriter
from docfp.writers.text_writer import NormalizedTextWriter, RawTextWriter
from docfp.extractors.tika_extractor import TikaDocumentTextExtractor

PASS_S = "\033[32mPASS\033[0m"
FAIL_S = "\033[31mFAIL\033[0m"
errors = []

def check(label, condition, detail=""):
    print(f"  [{'PASS' if condition else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not condition:
        errors.append(label)

source_uri = str(INPUT_DOC)
print(f"\n=== E2E Pipeline Test ===\nDocument : {INPUT_DOC.name}\nOutput   : {OUTPUT_ROOT}\n")

# Step 1
print("Step 1: Metadata + checksum")
meta = DocumentMetadataExtractor().extract(source_uri, pipeline_run_id=PIPELINE_RUN_ID)
meta = DocumentChecksumProcessor().compute_and_stamp(source_uri, meta)
json_path = MetadataJsonWriter().write(meta, OUTPUT_ROOT / "metadata")
check("document_id set", bool(meta.document_id), meta.document_id[:12] + "...")
check("metadata JSON written", json_path.exists())
check("mime_type detected", bool(meta.mime_type), meta.mime_type)

# Step 2
print("\nStep 2: Text extraction")
try:
    extracted = TikaDocumentTextExtractor().extract(source_uri)
    extracted.document_id = meta.document_id
    check("tika extraction ok", len(extracted.text) > 0, f"{len(extracted.text)} chars")
except Exception as exc:
    print(f"  [INFO] Tika unavailable; plain-text fallback")
    from docfp.models.extracted_text import ExtractedDocumentText
    raw_text = INPUT_DOC.read_text(encoding="utf-8")
    extracted = ExtractedDocumentText(
        document_id=meta.document_id, source_uri=source_uri, text=raw_text,
        metadata=meta, extraction_engine="plain-text-fallback", ocr_applied=False)
    check("plain-text fallback ok", len(extracted.text) > 0, f"{len(extracted.text)} chars")
txt_path = RawTextWriter().write(extracted, OUTPUT_ROOT / "text")
check("raw text file written", txt_path.exists())

# Step 3
print("\nStep 3: OCR decision")
needs_ocr = OcrDecisionProcessor(min_text_length=50, ocr_enabled=False).should_run_ocr(extracted.text, source_uri)
check("OCR skipped for text-rich .md", not needs_ocr)

# Step 4
print("\nStep 4: Normalization")
normalized = TextNormalizer(remove_stopwords=False).normalize(
    document_id=meta.document_id, source_uri=source_uri, text=extracted.text)
norm_path = NormalizedTextWriter().write(normalized, OUTPUT_ROOT / "normalized")
check("normalized text produced", len(normalized.text) > 0, f"{normalized.token_count} tokens")
check("normalization version set", normalized.normalization_version == "v1")
check("normalized file written", norm_path.exists())

# Step 5
print("\nStep 5: Tokenize + partition")
tokens = TokenizerProcessor().tokenize(normalized.text, meta.document_id)
check("tokens non-empty", len(tokens) > 0, f"{len(tokens)} tokens")
partitions = DocumentPartitionProcessor(partition_size=50_000).partition(tokens, meta.document_id)
check("at least 1 partition", len(partitions) >= 1, f"{len(partitions)} partitions")

# Step 6
print("\nStep 6: Shingling")
all_shingles = []
gen = WordShingleGenerator(shingle_size=SHINGLE_SIZE)
for pid, ptoks in partitions:
    all_shingles.extend(gen.generate(
        document_id=meta.document_id, source_uri=source_uri,
        file_name=INPUT_DOC.name, tokens=ptoks,
        partition_id=pid, partition_count=len(partitions)))
check("shingles generated", len(all_shingles) > 0, f"{len(all_shingles)} shingles")

# Step 7
print("\nStep 7: Shingle hashing")
ShingleHashProcessor().hash_records(all_shingles)
check("sha256 hashes populated", all(r.shingle_hash_sha256 for r in all_shingles))
check("xxhash64 hashes populated", all(r.shingle_hash64 != 0 for r in all_shingles))

# Step 8
print("\nStep 8: Write shingle Parquet")
parquet_path = ShingleParquetWriter().write(all_shingles, OUTPUT_ROOT / "shingles")
check("parquet written", parquet_path.exists(), str(parquet_path.relative_to(OUTPUT_ROOT)))

# Step 9 — hash signature (mirrors asset 9)
print("\nStep 9: Hash signature")
unique_hashes = sorted({r.shingle_hash_sha256 for r in all_shingles})
sig_sha256 = hashlib.sha256("".join(unique_hashes).encode("utf-8")).hexdigest()
check("hash signature computed", bool(sig_sha256), sig_sha256[:12] + "...")
check("unique hash count > 0", len(unique_hashes) > 0, f"{len(unique_hashes)} unique")

# Step 10 — minhash (mirrors asset 10)
print("\nStep 10: MinHash signature")
merged_mh = MinHashSignatureBuilder(num_perm=MINHASH_NUM_PERM).build(
    [r.shingle_hash64 for r in all_shingles], meta.document_id)
check("minhash built", merged_mh is not None)
check("minhash num_perm correct", merged_mh.hashvalues.shape[0] == MINHASH_NUM_PERM)

# Step 11 — write signature files
print("\nStep 11: Write signature files")
hash_sig_path, minhash_path = DocumentSignatureWriter().write(
    document_id=meta.document_id, source_uri=source_uri, file_name=INPUT_DOC.name,
    signature_version="v1", shingle_size=SHINGLE_SIZE,
    total_shingle_count=len(all_shingles), unique_shingle_hash_count=len(unique_hashes),
    hash_signature_sha256=sig_sha256, minhash=merged_mh,
    lsh_bucket_keys=[], partition_merge_status="single-partition",
    output_dir=OUTPUT_ROOT / "signatures")
check("hash_signature.json written", hash_sig_path.exists())
check("minhash.json written", minhash_path.exists())
with open(hash_sig_path) as f:
    sig_data = json.load(f)
for field in ("document_id", "hash_signature_sha256", "minhash_signature", "total_shingle_count"):
    check(f"  sig JSON has '{field}'", field in sig_data)

# Step 12 — LSH index
print("\nStep 12: LSH index")
lsh_builder = LshIndexBuilder(threshold=LSH_THRESHOLD, num_perm=MINHASH_NUM_PERM)
lsh = lsh_builder.build({meta.document_id: merged_mh})
lsh_path = lsh_builder.save(lsh, OUTPUT_ROOT / "indexes")
check("LSH index saved", lsh_path.exists())
lsh_loaded = lsh_builder.load(lsh_path)
query_results = lsh_builder.query(lsh_loaded, merged_mh)
check("LSH self-query returns document_id", meta.document_id in query_results, f"{query_results}")

# Step 13 — DLP retention (DLP_SAFE_MODE=False → shingles Parquet is KEPT)
print("\nStep 13: Shingle retention (DLP_SAFE_MODE={})".format(DLP_SAFE_MODE))
if DLP_SAFE_MODE:
    safe_copy = OUTPUT_ROOT / "shingles" / (parquet_path.stem + "_dlp_copy.parquet")
    shutil.copy(parquet_path, safe_copy)
    deleted = ShingleRetentionProcessor(dlp_safe_mode=True).process(safe_copy, meta.document_id)
    check("shingle parquet deleted in DLP-safe mode", deleted)
    check("original parquet still present", parquet_path.exists())
else:
    retained = ShingleRetentionProcessor(dlp_safe_mode=False).process(parquet_path, meta.document_id)
    check("shingle parquet retained (DLP_SAFE_MODE=False)", not retained)
    check("shingle parquet file exists on disk", parquet_path.exists())

# Summary
print(f"\n{'='*40}")
if errors:
    print(f"FAILED — {len(errors)} check(s) failed:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("ALL STEPS PASSED — full pipeline e2e test complete")
    print(f"\nArtifacts in: {OUTPUT_ROOT}")
    for f in sorted(OUTPUT_ROOT.rglob("*")):
        if f.is_file():
            rel = str(f.relative_to(OUTPUT_ROOT))
            size_kb = f.stat().st_size / 1024
            print(f"  {rel:<70} {size_kb:>8.1f} KB")
