#!/usr/bin/env python3
"""Offline private editorial snapshots. Never place archives in the website directory."""
import argparse
import datetime
import hashlib
import json
import os
import tempfile
from pathlib import Path
from validate_editorial_records import validate

def canonical(records):
    return (json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

def snapshot(records, timestamp):
    errors = validate(records)
    if errors:
        raise ValueError("Invalid editorial records: " + "; ".join(errors))
    if not isinstance(timestamp, str):
        raise ValueError("Timestamp required")
    try:
        moment = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if moment.tzinfo is None or moment.utcoffset() is None:
            raise ValueError("Timezone required")
    except ValueError as exc:
        raise ValueError("Timezone-aware ISO timestamp required") from exc
    data = canonical(records)
    return {"format": "world-wonder-private-backup-v1",
            "created_at": timestamp,
            "sha256": hashlib.sha256(data).hexdigest(),
            "records": records}

def verify(bundle):
    if not isinstance(bundle, dict) or set(bundle) != {"format", "created_at", "sha256", "records"}:
        raise ValueError("Invalid backup envelope")
    if bundle["format"] != "world-wonder-private-backup-v1":
        raise ValueError("Unsupported backup format")
    expected = snapshot(bundle["records"], bundle["created_at"])
    if bundle["sha256"] != expected["sha256"]:
        raise ValueError("Backup integrity mismatch")
    return bundle["records"]

def recovery_receipt(bundle, restored_records, timestamp):
    """Private provenance receipt without record content or identifying metadata."""
    verify(bundle)
    if canonical(restored_records) != canonical(bundle["records"]):
        raise ValueError("Restored records differ from verified backup")
    if not isinstance(timestamp, str):
        raise ValueError("Receipt timestamp required")
    try:
        moment = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if moment.tzinfo is None or moment.utcoffset() is None:
            raise ValueError("Timezone required")
    except ValueError as exc:
        raise ValueError("Timezone-aware receipt timestamp required") from exc
    return {
        "format": "world-wonder-recovery-receipt-v1",
        "backup_sha256": bundle["sha256"],
        "backup_created_at": bundle["created_at"],
        "restored_at": timestamp,
        "record_count": len(restored_records),
    }

def write_new(path, payload):
    if path.is_symlink() or path.exists():
        raise FileExistsError("Refusing to overwrite backup or symlink")
    if not path.parent.is_dir():
        raise ValueError("Backup parent directory must already exist")
    fd, temporary = tempfile.mkstemp(prefix=".wonder-backup-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if path.is_symlink() or path.exists():
            raise FileExistsError("Destination appeared during backup")
        os.link(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline private editorial backup and recovery")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("private_source", type=Path)
    create.add_argument("backup_destination", type=Path)
    check = sub.add_parser("verify")
    check.add_argument("backup", type=Path)
    restore = sub.add_parser("restore")
    restore.add_argument("backup", type=Path)
    restore.add_argument("new_private_destination", type=Path)
    restore.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "create":
        source = args.private_source.resolve(strict=True)
        if source.name == "public-catalogue.json":
            parser.error("Public catalogue is not a private source")
        records = json.loads(source.read_text(encoding="utf-8"))
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        write_new(args.backup_destination, snapshot(records, now))
        print("Private backup created")
    else:
        bundle = json.loads(args.backup.read_text(encoding="utf-8"))
        records = verify(bundle)
        if args.command == "restore":
            if args.new_private_destination.name == "public-catalogue.json":
                parser.error("Cannot restore into public catalogue")
            destination = args.new_private_destination
            receipt_path = args.receipt
            if destination.absolute() == receipt_path.absolute():
                parser.error("Receipt and restored file must differ")
            if receipt_path.is_symlink() or receipt_path.exists() or destination.is_symlink() or destination.exists():
                parser.error("Restore and receipt destinations must be new files")
            timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
            receipt = recovery_receipt(bundle, records, timestamp)
            write_new(destination, records)
            write_new(receipt_path, receipt)
            print("Verified backup restored; private provenance receipt created")
        else:
            print("Private backup verified")
if __name__ == "__main__":
    main()
