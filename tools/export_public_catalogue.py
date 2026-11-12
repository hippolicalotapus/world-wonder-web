#!/usr/bin/env python3
"""Export approved public editorial records without leaking internal fields."""
import json
import hashlib
import sys
import datetime
from public_export_audit import make_receipt
from editorial_backup import write_new, remove_if_unchanged
from private_input import load_private_json
from public_artifact_guard import validate_public_artifact
from export_path_guard import validate_export_paths
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
    if len(sys.argv) not in (6, 7):
        raise SystemExit("Usage: python3 tools/export_public_catalogue.py INPUT.json OUTPUT.json MANIFEST.json ATTESTATION.json PRIVATE_RECEIPT.json [TRUSTED_ANCHORS.json]")
    source = Path(sys.argv[1])
    destination = Path(sys.argv[2])
    validate_export_paths(source, Path(sys.argv[3]), Path(sys.argv[4]), destination, Path(sys.argv[5]))
    if source.resolve() == destination.resolve():
        raise SystemExit("Input and output must differ")
    records = load_private_json(source)
    manifest = load_private_json(Path(sys.argv[3]))
    from independent_review import validate_attestation
    attestation = load_private_json(Path(sys.argv[4]))
    validate_attestation(records, manifest, attestation)
    if len(sys.argv) == 7:
        from review_anchor_guard import verify_anchors
        anchor_path = Path(sys.argv[6]).absolute()
        private_paths = {source.absolute(), Path(sys.argv[3]).absolute(),
                         Path(sys.argv[4]).absolute(), destination.absolute(),
                         Path(sys.argv[5]).absolute()}
        if anchor_path in private_paths or anchor_path.parent == destination.absolute().parent:
            raise ValueError("Trusted audit anchors must be separate private input")
        verify_anchors(records, load_private_json(anchor_path))
    result = validate_public_artifact(guarded_export(records, manifest))
    if destination.name != "public-catalogue.json":
        raise SystemExit("Export destination must be public-catalogue.json")
    receipt_path = Path(sys.argv[5])
    if receipt_path.resolve() == destination.resolve() or receipt_path.name == "public-catalogue.json":
        raise SystemExit("Private receipt must differ from public catalogue")
    if destination.exists() or destination.is_symlink() or receipt_path.exists() or receipt_path.is_symlink():
        raise SystemExit("Catalogue and receipt must both be new files")
    if not destination.parent.is_dir() or not receipt_path.parent.is_dir():
        raise SystemExit("Output parent directories must exist")
    receipt = make_receipt(result, datetime.datetime.now(datetime.timezone.utc).isoformat())
    write_new(destination, result)
    stat = destination.lstat()
    identity = (stat.st_dev, stat.st_ino)
    try:
        write_new(receipt_path, receipt)
    except Exception:
        remove_if_unchanged(destination, identity)
        raise
    print(f"Exported {len(result)} published records")

if __name__ == "__main__":
    main()
