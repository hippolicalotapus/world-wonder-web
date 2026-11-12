#!/usr/bin/env python3
"""Offline second-reviewer attestation, not identity authentication."""
import datetime
import hashlib
import json
from editorial_backup import canonical

def make_attestation(records, manifest, reviewer, timestamp):
    from export_public_catalogue import guarded_export
    guarded_export(records, manifest)
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("Independent reviewer required")
    if not isinstance(timestamp, str):
        raise ValueError("Timezone-aware timestamp required")
    try:
        parsed = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("Timezone required")
    except ValueError as exc:
        raise ValueError("Valid timezone-aware timestamp required") from exc
    for record in records:
        if record.get("review_status") != "published":
            continue
        history = record.get("internal_review_history", [])
        if not isinstance(history, list):
            raise ValueError("Invalid review history")
        publishers = set()
        for entry in history:
            if not isinstance(entry, dict):
                raise ValueError("Invalid review history entry")
            if entry.get("to") not in ("approved", "published"):
                continue
            name = entry.get("reviewer")
            when = entry.get("timestamp")
            if not isinstance(name, str) or not name.strip() or not isinstance(when, str):
                raise ValueError("Invalid editorial approval entry")
            try:
                approval_time = datetime.datetime.fromisoformat(when.replace("Z", "+00:00"))
                if approval_time.tzinfo is None or approval_time.utcoffset() is None:
                    raise ValueError("Timezone required")
            except ValueError as exc:
                raise ValueError("Invalid editorial approval timestamp") from exc
            if approval_time > parsed:
                raise ValueError("Independent review predates editorial approval")
            publishers.add(name.strip().casefold())
        if not publishers:
            raise ValueError("Published record lacks recorded editorial approval")
        if reviewer.strip().casefold() in publishers:
            raise ValueError("Independent reviewer must differ from approving reviewer")
    return {"format": "world-wonder-independent-review-v1",
            "manifest_sha256": hashlib.sha256(canonical(manifest)).hexdigest(),
            "reviewer": reviewer.strip(), "reviewed_at": timestamp,
            "decision": "approved"}

def validate_attestation(records, manifest, attestation):
    if not isinstance(attestation, dict) or set(attestation) != {
        "format", "manifest_sha256", "reviewer", "reviewed_at", "decision"
    } or attestation.get("format") != "world-wonder-independent-review-v1" or attestation.get("decision") != "approved":
        raise ValueError("Invalid independent review attestation")
    expected = make_attestation(records, manifest, attestation["reviewer"], attestation["reviewed_at"])
    if expected != attestation:
        raise ValueError("Independent review attestation mismatch")
    return True
