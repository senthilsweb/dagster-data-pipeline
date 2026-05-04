"""Verify Dagster Definitions loads with all 12 assets."""
from docfp.dagster_defs import defs
assets = list(defs.resolve_all_asset_keys())
expected = {
    "source_document", "document_metadata_json", "raw_extracted_text",
    "ocr_extracted_text", "normalized_text", "document_shingles",
    "document_shingle_hashes", "document_shingle_parquet",
    "document_hash_signature", "document_minhash_signature",
    "lsh_index", "document_fingerprint_summary",
}
found = {k.path[-1] for k in assets}
assert found == expected, f"Missing: {expected - found}, Extra: {found - expected}"
print(f"Task 7 PASS - Dagster Definitions loaded with {len(assets)} assets:")
for k in sorted(found):
    print(f"  {k}")
