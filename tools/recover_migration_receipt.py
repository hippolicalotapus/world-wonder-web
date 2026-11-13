#!/usr/bin/env python3
"""Explicit create-only recovery of a missing private migration receipt.

Never changes source or migrated records. Refuses incomplete or mismatched
migrations, and verifies the inputs again immediately before writing.
"""
import argparse
from pathlib import Path
from atomic_private_receipt import write_new_receipt
from stable_private_input import read_stable, assert_unchanged
from migration_receipt import make_receipt
from reconcile_migration import reconcile
from review_anchor_cli import check_output
from private_file_locks import locked_inputs

def recover_receipt(original, migrated, receipt):
    original, migrated, receipt = (Path(p).absolute() for p in (original, migrated, receipt))
    # Preserve the reconciliation contract for incomplete pairs before locking.
    if not migrated.exists() or migrated.is_symlink():
        raise ValueError("Recovery requires an existing regular migrated file")
    with locked_inputs((original, migrated)) as reader:
        if reconcile(original, migrated, receipt) != "missing_receipt":
            raise ValueError("Recovery requires a verified migration with missing receipt")
        target = check_output(original, receipt)
        if target.parent.resolve() == migrated.parent.resolve():
            raise ValueError("Receipt must be separate from migrated records")
        source = reader.read_json(original)
        output = reader.read_json(migrated)
        proof = make_receipt(source, output)
        if reader.read_json(original) != source or reader.read_json(migrated) != output:
            raise ValueError('Private migration inputs changed during locked recovery')
        write_new_receipt(target, proof)
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
