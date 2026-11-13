#!/usr/bin/env python3
"""Explicit create-only recovery of a missing private migration receipt.

Never changes source or migrated records. Refuses incomplete or mismatched
migrations, and verifies the inputs again immediately before writing.
"""
import argparse
from pathlib import Path
from editorial_backup import write_new
from private_input import load_private_json
from migration_receipt import make_receipt
from reconcile_migration import reconcile
from review_anchor_cli import check_output

def recover_receipt(original, migrated, receipt):
    original, migrated, receipt = (Path(p).absolute() for p in (original, migrated, receipt))
    if reconcile(original, migrated, receipt) != "missing_receipt":
        raise ValueError("Recovery requires a verified migration with missing receipt")
    target = check_output(original, receipt)
    if target.parent.resolve() == migrated.parent.resolve():
        raise ValueError("Receipt must be separate from migrated records")
    before_source = original.stat()
    before_migrated = migrated.stat()
    source = load_private_json(original)
    output = load_private_json(migrated)
    proof = make_receipt(source, output)
    # Re-read both inputs and compare file identity to reduce stale-proof risk.
    if (original.stat().st_dev, original.stat().st_ino) != (before_source.st_dev, before_source.st_ino):
        raise ValueError("Original changed during receipt recovery")
    if (migrated.stat().st_dev, migrated.stat().st_ino) != (before_migrated.st_dev, before_migrated.st_ino):
        raise ValueError("Migrated file changed during receipt recovery")
    if load_private_json(original) != source or load_private_json(migrated) != output:
        raise ValueError("Migration inputs changed during receipt recovery")
    write_new(target, proof)
    return proof

def main(argv=None):
    parser = argparse.ArgumentParser(description="Recover only a verified missing private migration receipt")
    parser.add_argument("original", type=Path)
    parser.add_argument("migrated", type=Path)
    parser.add_argument("new_receipt", type=Path)
    parser.add_argument("--confirm-create", action="store_true")
    args = parser.parse_args(argv)
    if not args.confirm_create:
        parser.error("Explicit --confirm-create required; use reconcile_migration.py for read-only checks")
    recover_receipt(args.original, args.migrated, args.new_receipt)
    print("Recovered private receipt; original and migrated files unchanged")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
