"""Verify independently retained review-history heads for publication.

The anchors must be stored outside the editable editorial records and public
website. This validates consistency, not authentication of the anchor file.
"""
import re
from review_audit_chain import verify_history

FORMAT = "world-wonder-review-anchors-v1"

def prepare_anchors(records):
    if not isinstance(records, list):
        raise ValueError("Invalid editorial records")
    anchors = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str):
            raise ValueError("Invalid editorial record")
        key = record["id"]
        if not key or key in anchors:
            raise ValueError("Duplicate or missing record ID")
        history = record.get("internal_review_history", [])
        if history:
            anchors[key] = verify_history(history)
    return {"format": FORMAT, "heads": anchors}

def verify_anchors(records, anchor_file):
    if not isinstance(anchor_file, dict) or set(anchor_file) != {"format", "heads"} or anchor_file["format"] != FORMAT:
        raise ValueError("Invalid trusted anchor envelope")
    heads = anchor_file["heads"]
    if not isinstance(heads, dict) or any(not isinstance(k, str) or not k.strip() or not isinstance(v, str) or re.fullmatch(r"[0-9a-f]{64}", v) is None for k,v in heads.items()):
        raise ValueError("Invalid trusted anchor heads")
    expected = prepare_anchors(records)
    if expected["heads"] != heads:
        raise ValueError("Trusted audit anchor mismatch")
    for record in records:
        if record.get("review_status") == "published" and record["id"] not in heads:
            raise ValueError("Published record missing trusted audit anchor")
    return True
