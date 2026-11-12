#!/usr/bin/env python3
"""Export approved public editorial records without leaking internal fields."""
import json
import hashlib
import sys
from editorial_backup import write_new
from pathlib import Path
from validate_editorial_records import validate

PUBLIC_FIELDS = ("id", "title", "collection", "summary", "claim_type", "review_status")
SOURCE_FIELDS = ("title", "url", "publisher", "accessed_on", "source_type", "rights_status")

def export(records):
    errors = validate(records)
    if errors:
        raise ValueError("; ".join(errors))
    public = []
    for item in records:
        if item["review_status"] != "published":
            continue
        clean = {field: item[field] for field in PUBLIC_FIELDS}
        clean["sources"] = [
            {field: source[field] for field in SOURCE_FIELDS}
            for source in item["sources"]
        ]
        public.append(clean)
    return sorted(public, key=lambda item: item["id"])

def guarded_export(records, manifest):
    """Require explicit record IDs and exact source digest before publication."""
    if not isinstance(manifest, dict) or set(manifest) != {"format", "source_sha256", "publish_ids"}:
        raise ValueError("Invalid publication manifest")
    if manifest["format"] != "world-wonder-publication-manifest-v1":
        raise ValueError("Unsupported publication manifest")
    digest = hashlib.sha256(
        (json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    ).hexdigest()
    if manifest["source_sha256"] != digest:
        raise ValueError("Publication source changed since approval")
    ids = manifest["publish_ids"]
    if not isinstance(ids, list) or any(not isinstance(x, str) or not x.strip() for x in ids):
        raise ValueError("Invalid publication ID list")
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate publication IDs")
    result = export(records)
    actual = {item["id"] for item in result}
    if set(ids) != actual:
        raise ValueError("Publication IDs must exactly match published records")
    return result

def main():
    if len(sys.argv) != 5:
        raise SystemExit("Usage: python3 tools/export_public_catalogue.py INPUT.json OUTPUT.json MANIFEST.json ATTESTATION.json")
    source = Path(sys.argv[1])
    destination = Path(sys.argv[2])
    if source.resolve() == destination.resolve():
        raise SystemExit("Input and output must differ")
    records = json.loads(source.read_text(encoding="utf-8"))
    manifest = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
    from independent_review import validate_attestation
    attestation = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))
    validate_attestation(records, manifest, attestation)
    result = guarded_export(records, manifest)
    if destination.name != "public-catalogue.json":
        raise SystemExit("Export destination must be public-catalogue.json")
    write_new(destination, result)
    print(f"Exported {len(result)} published records")

if __name__ == "__main__":
    main()
