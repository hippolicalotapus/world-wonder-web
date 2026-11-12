"""Validate private editorial review history before independent publication approval.

Legacy partial histories remain supported; present entries must be coherent.
This is a consistency check, not a cryptographic tamper-proof log.
"""
import datetime
from editorial_workflow import NEXT

def check_history(history, reviewed_at):
    if not isinstance(history, list):
        raise ValueError("Invalid review history")
    approvers = set()
    previous_state = None
    previous_time = None
    for entry in history:
        if not isinstance(entry, dict):
            raise ValueError("Invalid review history entry")
        old, new = entry.get("from"), entry.get("to")
        if old not in NEXT or new not in NEXT[old]:
            raise ValueError("Invalid review history transition")
        if previous_state is not None and old != previous_state:
            raise ValueError("Disconnected review history")
        reviewer, reason, stamp = (entry.get("reviewer"), entry.get("reason"),
                                   entry.get("timestamp"))
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ValueError("Invalid editorial approval entry")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("Invalid review history reason")
        if not isinstance(stamp, str):
            raise ValueError("Invalid editorial approval timestamp")
        try:
            when = datetime.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if when.tzinfo is None or when.utcoffset() is None:
                raise ValueError("Timezone required")
        except ValueError as exc:
            raise ValueError("Invalid editorial approval timestamp") from exc
        if previous_time is not None and when < previous_time:
            raise ValueError("Review history timestamps out of order")
        if new in ("approved", "published"):
            if when > reviewed_at:
                raise ValueError("Independent review predates editorial approval")
            approvers.add(reviewer.strip().casefold())
        previous_state, previous_time = new, when
    if not approvers:
        raise ValueError("Published record lacks recorded editorial approval")
    return approvers
