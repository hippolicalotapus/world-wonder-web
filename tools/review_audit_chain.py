"""Hash-linked private editorial review history.

Hashes detect edits when compared with a trusted saved anchor; without an
external trusted anchor, an attacker can recompute the whole chain.
"""
import hashlib
from editorial_backup import canonical

GENESIS = "0" * 64
FIELDS = {"from", "to", "reviewer", "reason", "timestamp"}
CHAIN_FIELDS = FIELDS | {"previous_hash", "entry_hash"}

def digest(entry, previous):
    payload = {field: entry[field] for field in FIELDS}
    return hashlib.sha256(canonical({"previous_hash": previous, "entry": payload})).hexdigest()

def seal_history(history):
    if not isinstance(history, list):
        raise ValueError("Invalid review history")
    sealed = []
    previous = GENESIS
    for entry in history:
        if not isinstance(entry, dict) or not FIELDS.issubset(entry):
            raise ValueError("Invalid review history entry")
        if set(entry) not in (FIELDS, CHAIN_FIELDS):
            raise ValueError("Unexpected review history fields")
        base = {field: entry[field] for field in FIELDS}
        item = dict(base, previous_hash=previous, entry_hash=digest(base, previous))
        sealed.append(item)
        previous = item["entry_hash"]
    return sealed

def verify_history(history, trusted_head=None):
    if not isinstance(history, list):
        raise ValueError("Invalid review history")
    previous = GENESIS
    for entry in history:
        if not isinstance(entry, dict) or set(entry) != CHAIN_FIELDS:
            raise ValueError("Unsealed review history entry")
        if entry["previous_hash"] != previous or entry["entry_hash"] != digest(entry, previous):
            raise ValueError("Review history integrity mismatch")
        previous = entry["entry_hash"]
    if trusted_head is not None and trusted_head != previous:
        raise ValueError("Review history trusted anchor mismatch")
    return previous
