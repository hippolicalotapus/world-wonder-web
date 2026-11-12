"""Privacy-minimal offline public catalogue export audit receipts."""
import datetime
import hashlib
import json
from editorial_backup import canonical
from public_artifact_guard import validate_public_artifact

FIELDS = {"format", "catalogue_sha256", "record_count", "exported_at"}

def make_receipt(catalogue, timestamp):
    validate_public_artifact(catalogue)
    try:
        dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if dt.tzinfo is None or dt.utcoffset() is None:
            raise ValueError("Timezone required")
    except (AttributeError, ValueError, TypeError) as exc:
        raise ValueError("Timezone-aware export timestamp required") from exc
    return {"format": "world-wonder-public-export-receipt-v1",
            "catalogue_sha256": hashlib.sha256(canonical(catalogue)).hexdigest(),
            "record_count": len(catalogue), "exported_at": timestamp}

def verify_receipt(catalogue, receipt):
    if not isinstance(receipt, dict) or set(receipt) != FIELDS or receipt.get("format") != "world-wonder-public-export-receipt-v1":
        raise ValueError("Invalid public export receipt")
    expected = make_receipt(catalogue, receipt["exported_at"])
    if type(receipt["record_count"]) is not int or receipt != expected:
        raise ValueError("Public export receipt mismatch")
    return True
