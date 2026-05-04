"""Quick smoke-test for all Task 6 writers."""
import json, tempfile, pathlib, dataclasses
from docfp.models.document_metadata import DocumentMetadata
from docfp.models.extracted_text import ExtractedDocumentText
from docfp.models.normalized_text import NormalizedText
from docfp.models.shingle_record import ShingleRecord
from docfp.writers.metadata_json_writer import MetadataJsonWriter
from docfp.writers.text_writer import RawTextWriter, NormalizedTextWriter
from docfp.writers.shingle_parquet_writer import ShingleParquetWriter
from docfp.writers.document_signature_writer import DocumentSignatureWriter
from docfp.processors.minhash_signature_builder import MinHashSignatureBuilder
from datetime import datetime, timezone
import pyarrow.parquet as pq

DOC_ID = "a" * 64
FILE_NAME = "test_doc.pdf"
SRC_URI = "/tmp/test_doc.pdf"
NOW = datetime.now(timezone.utc).isoformat()

with tempfile.TemporaryDirectory() as td:
    out = pathlib.Path(td)

    # MetadataJsonWriter
    meta = DocumentMetadata(document_id=DOC_ID, source_uri=SRC_URI, file_name=FILE_NAME,
        file_size_bytes=1024, mime_type="application/pdf", extension=".pdf",
        created_at_utc=NOW)
    p = MetadataJsonWriter().write(meta, out / "metadata")
    assert p.name == "test_doc.metadata.json"
    loaded = json.loads(p.read_text())
    assert loaded["document_id"] == DOC_ID
    print(f"  MetadataJsonWriter OK: {p.name}")

    # RawTextWriter
    ext = ExtractedDocumentText(document_id=DOC_ID, source_uri=SRC_URI, text="Hello world")
    p = RawTextWriter().write(ext, out / "text")
    assert p.name == "test_doc.extracted.txt" and p.read_text() == "Hello world"
    print(f"  RawTextWriter OK: {p.name}")

    # NormalizedTextWriter
    norm = NormalizedText(document_id=DOC_ID, source_uri=SRC_URI, text="hello world", token_count=2)
    p = NormalizedTextWriter().write(norm, out / "normalized")
    assert p.name == "test_doc.normalized.txt" and p.read_text() == "hello world"
    print(f"  NormalizedTextWriter OK: {p.name}")

    # ShingleParquetWriter
    shingles = [ShingleRecord(document_id=DOC_ID, partition_id=0, partition_count=1,
        source_uri=SRC_URI, file_name=FILE_NAME, page_no=0, section_id=0,
        shingle_id=i, shingle_text=f"shingle {i}", shingle_hash64=i+1,
        shingle_hash_sha256="a"*64, token_start=i, token_end=i+4,
        char_start=0, char_end=9, normalization_version="v1", created_at_utc=NOW)
        for i in range(5)]
    p = ShingleParquetWriter().write(shingles, out / "shingles")
    assert p.name == "test_doc_shingle.parquet"
    t = pq.read_table(str(p))
    assert t.num_rows == 5
    print(f"  ShingleParquetWriter OK: {p.name} ({t.num_rows} rows)")

    # DocumentSignatureWriter
    mh = MinHashSignatureBuilder(num_perm=64).build([i+1 for i in range(5)], DOC_ID)
    sig_p, mh_p = DocumentSignatureWriter().write(
        document_id=DOC_ID, source_uri=SRC_URI, file_name=FILE_NAME,
        signature_version="v1", shingle_size=5, total_shingle_count=5,
        unique_shingle_hash_count=5, hash_signature_sha256="b"*64,
        minhash=mh, lsh_bucket_keys=["bucket1"], partition_merge_status="single-partition",
        output_dir=out / "signatures"
    )
    assert sig_p.name == "test_doc.hash_signature.json"
    assert mh_p.name == "test_doc.minhash.json"
    sig_data = json.loads(sig_p.read_text())
    assert sig_data["partition_merge_status"] == "single-partition"
    assert len(sig_data["minhash_signature"]) == 64
    print(f"  DocumentSignatureWriter OK: {sig_p.name}, {mh_p.name}")

print("Task 6 PASS - all writers OK")
