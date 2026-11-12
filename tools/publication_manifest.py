#!/usr/bin/env python3
"""Prepare private publication manifests without exporting or publishing."""
import argparse
import hashlib
import json
from pathlib import Path
from export_public_catalogue import export, guarded_export
from editorial_backup import canonical, write_new

def prepare(records):
    # Run existing editorial and rights gates first.
    published = export(records)
    return {
        "format": "world-wonder-publication-manifest-v1",
        "source_sha256": hashlib.sha256(canonical(records)).hexdigest(),
        "publish_ids": [item["id"] for item in published],
    }

def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline publication manifest preparation")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("prepare")
    create.add_argument("private_source", type=Path)
    create.add_argument("new_private_manifest", type=Path)
    check = sub.add_parser("validate")
    check.add_argument("private_source", type=Path)
    check.add_argument("private_manifest", type=Path)
    args = parser.parse_args(argv)
    source = args.private_source
    if source.is_symlink() or source.name == "public-catalogue.json":
        parser.error("Private source must not be a symlink or public catalogue")
    records = json.loads(source.read_text(encoding="utf-8"))
    if args.command == "prepare":
        manifest = prepare(records)
        if args.new_private_manifest.name == "public-catalogue.json":
            parser.error("Manifest cannot be public catalogue")
        write_new(args.new_private_manifest, manifest)
        print("Private manifest prepared; no publication performed")
    else:
        if args.private_manifest.is_symlink():
            parser.error("Refusing symlink manifest")
        manifest = json.loads(args.private_manifest.read_text(encoding="utf-8"))
        result = guarded_export(records, manifest)
        print(f"Manifest validated for {len(result)} records; no publication performed")

if __name__ == "__main__":
    main()
