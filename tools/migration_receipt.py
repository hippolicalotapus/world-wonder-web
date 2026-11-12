"""Privacy-minimal, independently verifiable legacy migration receipt."""
import hashlib
import re
from editorial_backup import canonical
from migrate_legacy_reviews import plan_migration

FORMAT = "world-wonder-legacy-migration-receipt-v1"
FIELDS = {"format", "source_sha256", "migrated_sha256", "record_count", "migrated_count"}

def checksum(records):
    return hashlib.sha256(canonical(records)).hexdigest()

def make_receipt(source, migrated):
    expected, changed = plan_migration(source)
    if canonical(expected) != canonical(migrated):
        raise ValueError("Migrated records do not match reviewed migration plan")
    return {"format": FORMAT, "source_sha256": checksum(source),
            "migrated_sha256": checksum(migrated),
            "record_count": len(source), "migrated_count": len(changed)}

def verify_receipt(source, migrated, receipt):
    if not isinstance(receipt, dict) or set(receipt) != FIELDS or receipt.get("format") != FORMAT:
        raise ValueError("Invalid migration receipt")
    if any(not isinstance(receipt[k], str) or re.fullmatch(r"[0-9a-f]{64}", receipt[k]) is None
           for k in ("source_sha256", "migrated_sha256")):
        raise ValueError("Invalid migration receipt hashes")
    if type(receipt["record_count"]) is not int or type(receipt["migrated_count"]) is not int:
        raise ValueError("Invalid migration receipt counts")
    if receipt != make_receipt(source, migrated):
        raise ValueError("Migration receipt mismatch")
    return True
