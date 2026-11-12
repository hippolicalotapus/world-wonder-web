#!/usr/bin/env python3
"""Read-only public catalogue/receipt reconciliation; prints status only."""
import argparse
import json
from pathlib import Path
from public_artifact_guard import validate_public_artifact
from public_export_audit import verify_receipt

def reconcile(catalogue, receipt):
    if catalogue is None and receipt is None:
        return "not_started"
    if catalogue is None:
        return "missing_catalogue"
    if receipt is None:
        return "missing_receipt"
    try:
        validate_public_artifact(catalogue)
    except (ValueError, TypeError, KeyError):
        return "invalid_catalogue"
    try:
        verify_receipt(catalogue, receipt)
    except (ValueError, TypeError, KeyError):
        if isinstance(receipt, dict) and receipt.get("format") == "world-wonder-public-export-receipt-v1":
            return "receipt_mismatch"
        return "invalid_receipt"
    return "verified"

def read_optional(path):
    if path.is_symlink():
        raise ValueError("Symlink input refused")
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError("Not a regular file")
    return json.loads(path.read_text(encoding="utf-8"))

def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only public export reconciliation")
    parser.add_argument("catalogue", type=Path)
    parser.add_argument("private_receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        status = reconcile(read_optional(args.catalogue), read_optional(args.private_receipt))
    except (OSError, ValueError, TypeError):
        status = "unreadable_or_invalid_file"
    print(status)
    return 0 if status == "verified" else 1

if __name__ == "__main__":
    raise SystemExit(main())
