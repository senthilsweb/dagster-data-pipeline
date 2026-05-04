"""Quick smoke-test for all Task 5 processors."""
from docfp.processors.text_normalizer import TextNormalizer
from docfp.processors.tokenizer import TokenizerProcessor
from docfp.processors.word_shingle_generator import WordShingleGenerator
from docfp.processors.shingle_hash_processor import ShingleHashProcessor
from docfp.processors.minhash_signature_builder import MinHashSignatureBuilder
from docfp.processors.lsh_index_builder import LshIndexBuilder
from docfp.processors.ocr_decision_processor import OcrDecisionProcessor
from docfp.processors.shingle_retention_processor import ShingleRetentionProcessor
from docfp.processors.document_partition_processor import DocumentPartitionProcessor
import tempfile, pathlib

RAW = "The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs."

norm = TextNormalizer().normalize("docid1", "/tmp/x.pdf", RAW)
assert norm.token_count == 17, f"token_count={norm.token_count}"
tokens = TokenizerProcessor().tokenize(norm.text, "docid1")
records = WordShingleGenerator(shingle_size=5).generate("docid1", "/tmp/x.pdf", "x.pdf", tokens)
assert len(records) == 13, f"shingle_count={len(records)}"
records = ShingleHashProcessor().hash_records(records)
assert all(len(r.shingle_hash_sha256) == 64 for r in records)
assert all(r.shingle_hash64 > 0 for r in records)

# determinism
r2 = ShingleHashProcessor().hash_records(
    WordShingleGenerator(shingle_size=5).generate("docid1", "/tmp/x.pdf", "x.pdf", tokens)
)
assert r2[0].shingle_hash_sha256 == records[0].shingle_hash_sha256

mh = MinHashSignatureBuilder(num_perm=64).build([r.shingle_hash64 for r in records], "docid1")
lsh_b = LshIndexBuilder(threshold=0.5, num_perm=64)
lsh = lsh_b.build({"docid1": mh})
assert "docid1" in lsh_b.query(lsh, mh)

parts = DocumentPartitionProcessor(partition_size=100).partition(tokens, "docid1")
assert len(parts) == 1 and parts[0][0] == 0

ocrp = OcrDecisionProcessor(min_text_length=50)
assert ocrp.should_run_ocr("", "/tmp/x.pdf") is True
assert ocrp.should_run_ocr("x" * 100, "/tmp/x.pdf") is False

with tempfile.TemporaryDirectory() as td:
    p = pathlib.Path(td) / "test_shingle.parquet"
    p.write_bytes(b"data")
    deleted = ShingleRetentionProcessor(dlp_safe_mode=True).process(p, "docid1")
    assert deleted and not p.exists()

print("Task 5 PASS - all 10 processors OK")
