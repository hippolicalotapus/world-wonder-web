#!/usr/bin/env python3
"""Read-only reconciliation of interrupted private editorial migrations.

Never creates, overwrites, or removes files. Does not authorize publication.
"""
import argparse
from pathlib import Path
from private_input import load_private_json
from migration_receipt import make_receipt, verify_receipt

def reconcile(original, migrated, receipt):
    paths = [Path(p).absolute() for p in (original, migrated, receipt)]
    if len(set(paths)) != 3:
        raise ValueError("Reconciliation paths must be distinct")
    if paths[1].name == "public-catalogue.json" or paths[2].name == "public-catalogue.json":
        raise ValueError("Private migration artifacts cannot be public catalogue")
    if paths[1].parent == paths[2].parent:
        raise ValueError("Migration and receipt must have separate directories")
    source = load_private_json(paths[0])
    migrated_exists = paths[1].exists() or paths[1].is_symlink()
    receipt_exists = paths[2].exists() or paths[2].is_symlink()
    if not migrated_exists and not receipt_exists:
        return "not_started"
    if not migrated_exists and receipt_exists:
        # Refuse to trust orphaned receipts even if they appear syntactically valid.
        load_private_json(paths[2])
        return "orphaned_receipt"
    output = load_private_json(paths[1])
    if not receipt_exists:
        # Only classify as recoverable if output exactly matches expected migration.
        make_receipt(source, output)
        return "missing_receipt"
    proof = load_private_json(paths[2])
    verify_receipt(source, output, proof)
    return "verified_complete"

def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only interrupted migration reconciliation")
    parser.add_argument("original", type=Path)
    parser.add_argument("migrated", type=Path)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args(argv)
    status = reconcile(args.original, args.migrated, args.receipt)
    print("Migration reconciliation: " + status + "; no files changed")
    return 0 if status in ("not_started", "verified_complete") else 2

if __name__ == "__main__":
    raise SystemExit(main())
