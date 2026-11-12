#!/usr/bin/env python3
"""Offline, create-only migration of legacy published editorial histories.

Never changes the source. New sealed records require separately retained
trusted anchors before publication. Existing publication approval is NOT
automatically renewed by migration.
"""
import argparse
import datetime
from pathlib import Path
from private_input import load_private_json
from editorial_backup import write_new, remove_if_unchanged
from review_audit_chain import seal_history, verify_history
from review_history_guard import check_history
from review_anchor_cli import check_output

def plan_migration(records):
    if not isinstance(records, list):
        raise ValueError("Invalid editorial records")
    now = datetime.datetime.now(datetime.timezone.utc)
    changed = []
    migrated = []
    seen = set()
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str) or not record["id"].strip():
            raise ValueError("Invalid record identifier")
        if record["id"] in seen:
            raise ValueError("Duplicate record identifier")
        seen.add(record["id"])
        item = dict(record)
        history = record.get("internal_review_history", [])
        if record.get("review_status") == "published":
            if not isinstance(history, list) or not history:
                raise ValueError("Published record lacks review history")
            check_history(history, now)
            if any(not isinstance(entry, dict) for entry in history):
                raise ValueError("Invalid review history entry")
            sealed = any("entry_hash" in entry or "previous_hash" in entry for entry in history)
            if sealed:
                verify_history(history)
            else:
                item["internal_review_history"] = seal_history(history)
                changed.append(record["id"])
        migrated.append(item)
    return migrated, changed

def main(argv=None):
    parser = argparse.ArgumentParser(description="Plan or create an offline sealed-history migration")
    parser.add_argument("private_source", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--confirm-create", action="store_true")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    records = load_private_json(args.private_source)
    result, changed = plan_migration(records)
    if args.confirm_create:
        if args.output is None:
            parser.error("--confirm-create requires --output")
        destination = check_output(args.private_source, args.output)
        if not changed:
            raise ValueError("No legacy published histories require migration")
        if args.receipt is None:
            raise ValueError("Migration receipt path required for confirmed migration")
        from migration_receipt import make_receipt
        receipt_path = check_output(args.private_source, args.receipt)
        if receipt_path == destination or receipt_path.parent == destination.parent:
            raise ValueError("Receipt must be separate from migrated records")
        receipt = make_receipt(records, result)
        write_new(destination, result)
        identity = destination.lstat()
        try:
            write_new(receipt_path, receipt)
        except Exception:
            remove_if_unchanged(destination, (identity.st_dev, identity.st_ino))
            raise
        print(f"Created private migrated copy: {len(changed)} sealed published histories; source unchanged")
    else:
        if args.output is not None or args.receipt is not None:
            parser.error("--output and --receipt require --confirm-create")
        print(f"Dry run: {len(changed)} legacy published histories eligible; no files changed")
    return len(changed)

if __name__ == "__main__":
    main()
