#!/usr/bin/env python3
"""Read-only reconciliation of a private restored file and provenance receipt."""
import argparse
import json
from pathlib import Path
from editorial_backup import canonical, verify

def reconcile(bundle, restored, receipt):
    """Return a safe status code; never return record contents."""
    try:
        source = verify(bundle)
    except (ValueError, TypeError, KeyError):
        return "invalid_backup"
    if restored is None and receipt is None:
        return "not_started"
    if restored is None:
        return "missing_restored_records"
    if receipt is None:
        return "missing_receipt"
    if not isinstance(restored, list) or canonical(restored) != canonical(source):
        return "restored_data_mismatch"
    if not isinstance(receipt, dict) or set(receipt) != {
        "format", "backup_sha256", "backup_created_at", "restored_at", "record_count"
    }:
        return "invalid_receipt"
    if receipt["format"] != "world-wonder-recovery-receipt-v1":
        return "invalid_receipt"
    if (receipt["backup_sha256"] != bundle["sha256"]
            or receipt["backup_created_at"] != bundle["created_at"]
            or type(receipt["record_count"]) is not int
            or receipt["record_count"] != len(restored)):
        return "receipt_mismatch"
    try:
        from editorial_backup import recovery_receipt
        recovery_receipt(bundle, restored, receipt["restored_at"])
    except (ValueError, TypeError):
        return "invalid_receipt"
    return "verified"

def read_optional(path):
    if path.is_symlink():
        raise ValueError("Refusing symlink input")
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only private recovery reconciliation")
    parser.add_argument("backup", type=Path)
    parser.add_argument("restored", type=Path)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.backup.is_symlink():
            raise ValueError("Refusing symlink backup")
        bundle = json.loads(args.backup.read_text(encoding="utf-8"))
        status = reconcile(bundle, read_optional(args.restored), read_optional(args.receipt))
    except (OSError, ValueError, json.JSONDecodeError):
        status = "unreadable_or_invalid_file"
    print(status)
    return 0 if status in ("verified", "not_started") else 1

if __name__ == "__main__":
    raise SystemExit(main())
