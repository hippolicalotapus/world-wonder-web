#!/usr/bin/env python3
"""Offline create-only anchor preparation and read-only verification.

Preparation is NOT independent trust establishment. Transfer the resulting
anchor to separately controlled storage after reviewing the source.
"""
import argparse
import os
from pathlib import Path
from editorial_backup import write_new
from private_input import load_private_json
from review_anchor_guard import prepare_anchors, verify_anchors

def check_output(source, output):
    source = Path(source).absolute()
    output = Path(output).absolute()
    if output.name == "public-catalogue.json" or output == source:
        raise ValueError("Invalid private anchor output path")
    if output.parent.resolve() == source.parent.resolve():
        raise ValueError("Anchor must be stored outside the editable source directory")
    if not output.parent.is_dir() or output.parent.resolve() != output.parent:
        raise ValueError("Anchor directory must exist and not be a symlink")
    if output.exists() or output.is_symlink():
        raise FileExistsError("Anchor output must be new")
    # Refuse known repository roots and their descendants.
    for parent in (output.parent.resolve(), *output.parent.resolve().parents):
        if (parent / ".git").exists():
            raise ValueError("Anchor must not be written inside a Git repository")
    return output

def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline private audit-anchor workflow")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("prepare")
    create.add_argument("private_source", type=Path)
    create.add_argument("new_private_anchor", type=Path)
    check = commands.add_parser("verify")
    check.add_argument("private_source", type=Path)
    check.add_argument("trusted_anchor", type=Path)
    args = parser.parse_args(argv)
    records = load_private_json(args.private_source)
    if args.command == "prepare":
        target = check_output(args.private_source, args.new_private_anchor)
        anchors = prepare_anchors(records)
        # Do not produce an apparently trusted anchor for unsealed published data.
        for record in records:
            if record.get("review_status") == "published" and record["id"] not in anchors["heads"]:
                raise ValueError("Published record requires sealed review history")
        write_new(target, anchors)
        print("Private anchor prepared; independent retention still required")
    else:
        anchors = load_private_json(args.trusted_anchor)
        verify_anchors(records, anchors)
        print("Trusted audit anchor matches; no files changed")

if __name__ == "__main__":
    main()
