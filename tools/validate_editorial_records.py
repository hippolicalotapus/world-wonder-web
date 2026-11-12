#!/usr/bin/env python3
"""Validate source-backed World Wonder Web editorial records (stdlib only)."""
import datetime
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

CLAIMS = {"documented_event", "first_person_testimony", "belief_or_tradition", "unverified_report"}
STATES = {"draft", "fact_check", "rights_review", "approved", "published"}
SOURCE_TYPES = {"primary", "secondary", "testimony"}
RIGHTS = {"link_only", "licensed", "public_domain", "permission_pending"}

def validate(records):
    errors, ids = [], set()
    if not isinstance(records, list):
        return ["root must be an array of records"]
    for n, record in enumerate(records):
        at = f"records[{n}]"
        if not isinstance(record, dict):
            errors.append(f"{at}: expected object")
            continue
        for field in ("id", "title", "collection", "summary"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                errors.append(f"{at}: missing {field}")
        identity = record.get("id")
        if isinstance(identity, str):
            if identity in ids:
                errors.append(f"{at}: duplicate id")
            ids.add(identity)
        if record.get("claim_type") not in CLAIMS:
            errors.append(f"{at}: invalid claim_type")
        state = record.get("review_status")
        if state not in STATES:
            errors.append(f"{at}: invalid review_status")
        sources = record.get("sources")
        if not isinstance(sources, list):
            errors.append(f"{at}: sources must be an array")
            continue
        if state == "published" and not sources:
            errors.append(f"{at}: published records require sources")
        for i, source in enumerate(sources):
            where = f"{at}.sources[{i}]"
            if not isinstance(source, dict):
                errors.append(f"{where}: expected object")
                continue
            for field in ("title", "publisher"):
                if not isinstance(source.get(field), str) or not source[field].strip():
                    errors.append(f"{where}: missing {field}")
            url = source.get("url")
            if not isinstance(url, str) or urlparse(url).scheme not in ("https", "http") or not urlparse(url).netloc:
                errors.append(f"{where}: invalid source URL")
            try:
                datetime.date.fromisoformat(source["accessed_on"])
            except (KeyError, TypeError, ValueError):
                errors.append(f"{where}: invalid accessed_on date")
            if source.get("source_type") not in SOURCE_TYPES:
                errors.append(f"{where}: invalid source_type")
            if source.get("rights_status") not in RIGHTS:
                errors.append(f"{where}: invalid rights_status")
            if state == "published" and source.get("rights_status") == "permission_pending":
                errors.append(f"{where}: pending rights cannot be published")
    return errors

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 tools/validate_editorial_records.py records.json")
    records = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    errors = validate(records)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(1)
    print(f"Validated {len(records)} editorial records")

if __name__ == "__main__":
    main()
