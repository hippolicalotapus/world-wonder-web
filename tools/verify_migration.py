#!/usr/bin/env python3
"""Read-only offline verification of private legacy migration receipt."""
import argparse
from pathlib import Path
from stable_private_input import read_stable, assert_unchanged
from migration_receipt import verify_receipt
from private_file_locks import locked_inputs

def main(argv=None):
    parser=argparse.ArgumentParser(description="Verify private legacy migration without changing files")
    parser.add_argument("original",type=Path)
    parser.add_argument("migrated",type=Path)
    parser.add_argument("private_receipt",type=Path)
    args=parser.parse_args(argv)
    paths=(args.original.absolute(),args.migrated.absolute(),args.private_receipt.absolute())
    if len(set(paths)) != 3:
        raise ValueError("Verification inputs must be distinct")
    with locked_inputs(paths) as reader:
        snapshots = [reader.read_json(p) for p in paths]
        verify_receipt(*snapshots)
        if [reader.read_json(p) for p in paths] != snapshots:
            raise ValueError('Private inputs changed during locked verification')
    print("Migration verified; no files changed")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
