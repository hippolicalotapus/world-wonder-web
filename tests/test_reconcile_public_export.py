import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from public_export_audit import make_receipt
from reconcile_public_export import reconcile, read_optional, main

NOW = "2026-11-12T23:00:00Z"
def fixture():
    return [{"id": "fictional", "title": "Fixture", "collection": "Kindness",
             "summary": "Synthetic", "claim_type": "unverified_report",
             "review_status": "published",
             "sources": [{"title": "Example", "url": "https://example.org",
                          "publisher": "Example", "accessed_on": "2026-11-12",
                          "source_type": "secondary", "rights_status": "link_only"}]}]

class ReconcilePublicExportTests(unittest.TestCase):
    def setUp(self):
        self.catalogue = fixture()
        self.receipt = make_receipt(self.catalogue, NOW)

    def test_verified(self):
        self.assertEqual(reconcile(self.catalogue, self.receipt), "verified")

    def test_not_started(self):
        self.assertEqual(reconcile(None, None), "not_started")

    def test_missing_catalogue(self):
        self.assertEqual(reconcile(None, self.receipt), "missing_catalogue")

    def test_missing_receipt(self):
        self.assertEqual(reconcile(self.catalogue, None), "missing_receipt")

    def test_modified_catalogue(self):
        self.catalogue[0]["summary"] = "Changed"
        self.assertEqual(reconcile(self.catalogue, self.receipt), "receipt_mismatch")

    def test_invalid_catalogue(self):
        self.catalogue[0]["internal_notes"] = "private"
        self.assertEqual(reconcile(self.catalogue, self.receipt), "invalid_catalogue")

    def test_wrong_receipt(self):
        self.receipt["catalogue_sha256"] = "0" * 64
        self.assertEqual(reconcile(self.catalogue, self.receipt), "receipt_mismatch")

    def test_invalid_receipt_format(self):
        self.receipt["format"] = "other"
        self.assertEqual(reconcile(self.catalogue, self.receipt), "invalid_receipt")

    def test_read_only_does_not_change_files(self):
        with tempfile.TemporaryDirectory() as folder:
            catalogue = Path(folder) / "public-catalogue.json"
            receipt = Path(folder) / "receipt.json"
            catalogue.write_text(json.dumps(self.catalogue))
            receipt.write_text(json.dumps(self.receipt))
            before = (catalogue.read_bytes(), receipt.read_bytes())
            self.assertEqual(main([str(catalogue), str(receipt)]), 0)
            self.assertEqual((catalogue.read_bytes(), receipt.read_bytes()), before)

    def test_symlink_input_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            original = Path(folder) / "original.json"
            original.write_text("[]")
            link = Path(folder) / "linked.json"
            link.symlink_to(original)
            with self.assertRaises(ValueError):
                read_optional(link)

if __name__ == "__main__":
    unittest.main()
