#!/usr/bin/env python3
"""Local-only editorial review console. Never serve this tool from the public website."""
import argparse
import datetime
import json
import os
import tempfile
from pathlib import Path
from editorial_workflow import NEXT, transition
from validate_editorial_records import validate

def review_records(records, record_id, state, reviewer, reason, timestamp):
    if not isinstance(records, list):
        raise ValueError("Private editorial file must be an array")
    matches = [i for i, r in enumerate(records) if isinstance(r, dict) and r.get("id") == record_id]
    if len(matches) != 1:
        raise ValueError("Record ID must match exactly one private record")
    updated = list(records)
    updated[matches[0]] = transition(records[matches[0]], state, reviewer, reason, timestamp)
    errors = validate(updated)
    if errors:
        raise ValueError("Editorial validation failed: " + "; ".join(errors))
    return updated

def safe_write(destination, records):
    """Atomic replace with owner-only permissions; refuse symlink destinations."""
    if destination.is_symlink():
        raise ValueError("Refusing symlink output")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".editorial-", suffix=".json", dir=destination.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump(records, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, destination)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def main(argv=None):
    parser = argparse.ArgumentParser(description="Private local editorial review console")
    parser.add_argument("private_file", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("queue")
    decision = sub.add_parser("decide")
    decision.add_argument("--id", required=True)
    decision.add_argument("--state", required=True, choices=sorted(NEXT))
    decision.add_argument("--reviewer", required=True)
    decision.add_argument("--reason", required=True)
    decision.add_argument("--timestamp", default=None)
    decision.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    source = args.private_file.resolve(strict=True)
    if source.name == "public-catalogue.json":
        parser.error("Public catalogue is not an editorial source")
    records = json.loads(source.read_text(encoding="utf-8"))
    if args.command == "queue":
        if not isinstance(records, list):
            raise ValueError("Private editorial file must be an array")
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("Invalid record")
            print(f"{record.get('id', '[missing id]')} | {record.get('review_status', '[missing status]')}")
        return
    destination = args.output.absolute()
    if destination == source or destination.name == "public-catalogue.json":
        parser.error("Output must be a separate private file, not the source or public catalogue")
    timestamp = args.timestamp or datetime.datetime.now(datetime.timezone.utc).isoformat()
    updated = review_records(records, args.id, args.state, args.reviewer, args.reason, timestamp)
    safe_write(destination, updated)
    print("Private review decision saved to separate file; public catalogue unchanged.")

if __name__ == "__main__":
    main()
