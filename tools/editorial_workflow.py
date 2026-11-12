#!/usr/bin/env python3
"""Offline editorial review transitions; audit history stays private."""
import datetime

STATES = ("draft", "fact_check", "rights_review", "approved", "published", "rejected")
NEXT = {
    "draft": {"fact_check", "rejected"},
    "fact_check": {"rights_review", "draft", "rejected"},
    "rights_review": {"approved", "fact_check", "rejected"},
    "approved": {"published", "rights_review", "rejected"},
    "published": {"rights_review"},
    "rejected": {"draft"},
}

def transition(record, new_state, reviewer, reason, timestamp):
    if not isinstance(record, dict):
        raise ValueError("Record must be an object")
    old = record.get("review_status")
    if old not in NEXT or new_state not in NEXT[old]:
        raise ValueError("Invalid editorial transition")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("Reviewer is required")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Decision reason is required")
    if not isinstance(timestamp, str):
        raise ValueError("ISO timestamp required")
    try:
        parsed = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("Timezone required")
    except (TypeError, ValueError) as exc:
        raise ValueError("Valid timezone-aware ISO timestamp required") from exc
    if new_state in ("approved", "published"):
        from validate_editorial_records import validate
        candidate = dict(record, review_status="published")
        errors = validate([candidate])
        if errors:
            raise ValueError("Publication gates failed: " + "; ".join(errors))
    history = record.get("internal_review_history", [])
    if not isinstance(history, list):
        raise ValueError("Invalid review history")
    updated = dict(record)
    updated["review_status"] = new_state
    updated["internal_review_history"] = [*history, {
        "from": old, "to": new_state, "reviewer": reviewer.strip(),
        "reason": reason.strip(), "timestamp": timestamp
    }]
    return updated
