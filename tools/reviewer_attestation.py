#!/usr/bin/env python3
"""Offline preparation and validation of private independent review attestations."""
import argparse
import datetime
import json
from pathlib import Path
from editorial_backup import write_new
from private_input import load_private_json
from independent_review import make_attestation, validate_attestation

def load_private(path):
    return load_private_json(path)

def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline independent reviewer attestation")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("private_source", type=Path)
    prepare.add_argument("private_manifest", type=Path)
    prepare.add_argument("new_private_attestation", type=Path)
    prepare.add_argument("--reviewer", required=True)
    prepare.add_argument("--timestamp", default=None)
    check = sub.add_parser("validate")
    check.add_argument("private_source", type=Path)
    check.add_argument("private_manifest", type=Path)
    check.add_argument("private_attestation", type=Path)
    args = parser.parse_args(argv)
    records = load_private(args.private_source)
    manifest = load_private(args.private_manifest)
    if args.command == "prepare":
        if args.new_private_attestation.name == "public-catalogue.json":
            parser.error("Attestation cannot be public catalogue")
        timestamp = args.timestamp or datetime.datetime.now(datetime.timezone.utc).isoformat()
        attestation = make_attestation(records, manifest, args.reviewer, timestamp)
        write_new(args.new_private_attestation, attestation)
        print("Private attestation prepared; no publication performed")
    else:
        attestation = load_private(args.private_attestation)
        validate_attestation(records, manifest, attestation)
        print("Independent review attestation validated; no publication performed")

if __name__ == "__main__":
    main()
