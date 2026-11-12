#!/usr/bin/env python3
"""Offline checks for World Wonder Web editorial publishing gates."""
import importlib.util
from pathlib import Path
import unittest

module_path = Path(__file__).resolve().parents[1] / "tools" / "validate_editorial_records.py"
spec = importlib.util.spec_from_file_location("editorial_validator", module_path)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

def record(state="published", rights="link_only"):
    return {"id": "example-1", "title": "Example", "collection": "Survival",
            "summary": "Illustrative fixture only", "claim_type": "unverified_report",
            "review_status": state,
            "sources": [{"title": "Source", "url": "https://example.org/report",
                         "publisher": "Example", "accessed_on": "2026-11-12",
                         "source_type": "secondary", "rights_status": rights}]}

class EditorialValidationTests(unittest.TestCase):
    def test_valid_sourced_record(self):
        self.assertEqual(validator.validate([record()]), [])

    def test_published_record_requires_sources(self):
        item = record()
        item["sources"] = []
        self.assertTrue(validator.validate([item]))

    def test_pending_rights_cannot_publish(self):
        self.assertTrue(validator.validate([record(rights="permission_pending")]))

    def test_draft_can_have_pending_rights(self):
        self.assertEqual(validator.validate([record(state="draft", rights="permission_pending")]), [])

    def test_duplicate_ids_rejected(self):
        self.assertTrue(any("duplicate id" in e for e in validator.validate([record(), record()])))

    def test_invalid_source_url_rejected(self):
        item = record()
        item["sources"][0]["url"] = "file:///private.txt"
        self.assertTrue(validator.validate([item]))


    def test_documented_event_requires_primary_source(self):
        item = record()
        item["claim_type"] = "documented_event"
        self.assertTrue(any("primary source" in e for e in validator.validate([item])))

    def test_documented_event_with_primary_source_passes(self):
        item = record()
        item["claim_type"] = "documented_event"
        item["sources"][0]["source_type"] = "primary"
        self.assertEqual(validator.validate([item]), [])

if __name__ == "__main__":
    unittest.main()
