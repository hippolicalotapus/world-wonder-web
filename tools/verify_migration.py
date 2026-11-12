#!/usr/bin/env python3
"""Read-only offline verification of private legacy migration receipt."""
import argparse
from pathlib import Path
from private_input import load_private_json
from migration_receipt import verify_receipt

def main(argv=None):
    parser=argparse.ArgumentParser(description="Verify private legacy migration without changing files")
    parser.add_argument("original",type=Path)
    parser.add_argument("migrated",type=Path)
    parser.add_argument("private_receipt",type=Path)
    args=parser.parse_args(argv)
    paths=(args.original.absolute(),args.migrated.absolute(),args.private_receipt.absolute())
    if len(set(paths)) != 3:
        raise ValueError("Verification inputs must be distinct")
    verify_receipt(*(load_private_json(p) for p in paths))
    print("Migration verified; no files changed")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
