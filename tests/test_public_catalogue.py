#!/usr/bin/env python3
"""Regression coverage for the public catalogue privacy boundary."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
import sys
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location("public_export", TOOLS / "export_public_catalogue.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def record(state="published"):
    return {
        "id": "wonder-1", "title": "Illustrative record", "collection": "Kindness",
        "summary": "Synthetic test fixture", "claim_type": "unverified_report",
        "review_status": state, "email": "private@example.org" if state == "draft" else None,
        "sources": [{"title": "Example", "url": "https://example.org/story",
                     "publisher": "Example", "accessed_on": "2026-11-12",
                     "source_type": "secondary", "rights_status": "link_only",
                     "internal_notes": "never export"}],
        "internal_review_history": [{"reviewer": "private", "reason": "fixture"}],
    }

class PublicCatalogueTests(unittest.TestCase):
    def test_only_published_records_are_exported(self):
        published = record()
        published.pop("email")
        result = module.export([record("draft"), published])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "wonder-1")

    def test_internal_metadata_and_source_notes_are_stripped(self):
        item = record()
        item.pop("email")
        exported = module.export([item])[0]
        self.assertNotIn("internal_review_history", exported)
        self.assertNotIn("internal_notes", exported["sources"][0])
        self.assertEqual(set(exported), set(module.PUBLIC_FIELDS) | {"sources"})
        self.assertEqual(set(exported["sources"][0]), set(module.SOURCE_FIELDS))

    def test_published_private_contact_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "private field email"):
            module.export([record()])

    def test_pending_rights_are_rejected(self):
        item = record()
        item.pop("email")
        item["sources"][0]["rights_status"] = "permission_pending"
        with self.assertRaisesRegex(ValueError, "pending rights"):
            module.export([item])

    def test_export_order_is_stable(self):
        first = record()
        first.pop("email")
        second = dict(first, id="wonder-0")
        self.assertEqual([x["id"] for x in module.export([first, second])],
                         ["wonder-0", "wonder-1"])

if __name__ == "__main__":
    unittest.main()
