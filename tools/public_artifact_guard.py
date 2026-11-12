"""Strict final-artifact validation before any public catalogue write."""
from urllib.parse import urlsplit
from datetime import date

RECORD_FIELDS = {"id", "title", "collection", "summary", "claim_type", "review_status", "sources"}
SOURCE_FIELDS = {"title", "url", "publisher", "accessed_on", "source_type", "rights_status"}
CLAIMS = {"documented_event", "first_person_testimony", "belief_or_tradition", "unverified_report"}
SOURCE_TYPES = {"primary", "secondary", "testimony"}
RIGHTS = {"link_only", "licensed", "public_domain"}

def validate_public_artifact(records):
    if not isinstance(records, list):
        raise ValueError("Public catalogue must be an array")
    ids = set()
    for record in records:
        if not isinstance(record, dict) or set(record) != RECORD_FIELDS:
            raise ValueError("Unexpected or missing public record fields")
        if record["review_status"] != "published":
            raise ValueError("Unpublished record in public catalogue")
        for key in ("id", "title", "collection", "summary"):
            if not isinstance(record[key], str) or not record[key].strip():
                raise ValueError("Invalid public field: " + key)
        if record["id"] in ids:
            raise ValueError("Duplicate public record ID")
        ids.add(record["id"])
        if record["claim_type"] not in CLAIMS:
            raise ValueError("Invalid claim classification")
        sources = record["sources"]
        if not isinstance(sources, list) or not sources:
            raise ValueError("Public record requires sources")
        for source in sources:
            if not isinstance(source, dict) or set(source) != SOURCE_FIELDS:
                raise ValueError("Unexpected or missing public source fields")
            if any(not isinstance(source[k], str) or not source[k].strip() for k in SOURCE_FIELDS):
                raise ValueError("Invalid public source value")
            try:
                url = urlsplit(source["url"])
                if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password:
                    raise ValueError("Unsafe public source URL")
                date.fromisoformat(source["accessed_on"])
            except (ValueError, TypeError) as exc:
                raise ValueError("Invalid public source URL or date") from exc
            if source["source_type"] not in SOURCE_TYPES or source["rights_status"] not in RIGHTS:
                raise ValueError("Invalid public source classification or rights")
        if record["claim_type"] == "documented_event" and not any(
            source["source_type"] == "primary" for source in sources
        ):
            raise ValueError("Documented event requires primary source")
    return records
