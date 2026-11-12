import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from public_export_audit import make_receipt, verify_receipt

NOW = "2026-11-12T23:00:00Z"
def fixture():
    return [{"id": "fictional", "title": "Fixture", "collection": "Kindness",
             "summary": "Synthetic", "claim_type": "unverified_report", "review_status": "published",
             "sources": [{"title": "Example", "url": "https://example.org",
                          "publisher": "Example", "accessed_on": "2026-11-12",
                          "source_type": "secondary", "rights_status": "link_only"}]}]

class PublicExportAuditTests(unittest.TestCase):
    def test_receipt_verifies(self):
        catalogue = fixture()
        self.assertTrue(verify_receipt(catalogue, make_receipt(catalogue, NOW)))

    def test_no_private_content_in_receipt(self):
        receipt = make_receipt(fixture(), NOW)
        self.assertEqual(set(receipt), {"format", "catalogue_sha256", "record_count", "exported_at"})
        self.assertNotIn("Fixture", str(receipt))

    def test_tampered_catalogue_rejected(self):
        catalogue = fixture()
        receipt = make_receipt(catalogue, NOW)
        catalogue[0]["summary"] = "Modified"
        with self.assertRaisesRegex(ValueError, "mismatch"):
            verify_receipt(catalogue, receipt)

    def test_extra_receipt_field_rejected(self):
        catalogue = fixture()
        receipt = make_receipt(catalogue, NOW)
        receipt["reviewer_email"] = "private@example.org"
        with self.assertRaisesRegex(ValueError, "Invalid"):
            verify_receipt(catalogue, receipt)

    def test_invalid_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError, "timestamp"):
            make_receipt(fixture(), "2026-11-12T23:00:00")

    def test_unpublished_catalogue_rejected(self):
        catalogue = fixture()
        catalogue[0]["review_status"] = "draft"
        with self.assertRaisesRegex(ValueError, "Unpublished"):
            make_receipt(catalogue, NOW)

if __name__ == "__main__":
    unittest.main()
