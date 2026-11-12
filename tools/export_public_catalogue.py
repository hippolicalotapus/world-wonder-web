#!/usr/bin/env python3
"""Export approved public editorial records without leaking internal fields."""
import json
import sys
from pathlib import Path
from validate_editorial_records import validate

PUBLIC_FIELDS = ("id", "title", "collection", "summary", "claim_type", "review_status")
SOURCE_FIELDS = ("title", "url", "publisher", "accessed_on", "source_type", "rights_status")

def export(records):
    errors = validate(records)
    if errors:
        raise ValueError("; ".join(errors))
    public = []
    for item in records:
        if item["review_status"] != "published":
            continue
        clean = {field: item[field] for field in PUBLIC_FIELDS}
        clean["sources"] = [
            {field: source[field] for field in SOURCE_FIELDS}
            for source in item["sources"]
        ]
        public.append(clean)
    return sorted(public, key=lambda item: item["id"])

def main():
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python3 tools/export_public_catalogue.py INPUT.json OUTPUT.json")
    source = Path(sys.argv[1])
    destination = Path(sys.argv[2])
    if source.resolve() == destination.resolve():
        raise SystemExit("Input and output must differ")
    records = json.loads(source.read_text(encoding="utf-8"))
    result = export(records)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(result)} published records")

if __name__ == "__main__":
    main()
