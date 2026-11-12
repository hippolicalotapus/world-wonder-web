import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from public_artifact_guard import validate_public_artifact

def fixture():
    return [{"id": "fictional", "title": "Fictional", "collection": "Kindness",
             "summary": "Fixture", "claim_type": "unverified_report",
             "review_status": "published",
             "sources": [{"title": "Example", "url": "https://example.org/story",
                          "publisher": "Example", "accessed_on": "2026-11-12",
                          "source_type": "secondary", "rights_status": "link_only"}]}]

class PublicArtifactGuardTests(unittest.TestCase):
    def test_valid_artifact(self):
        records = fixture()
        self.assertEqual(validate_public_artifact(records), records)

    def test_private_record_field_rejected(self):
        records = fixture()
        records[0]["internal_review_history"] = [{"reviewer": "private"}]
        with self.assertRaisesRegex(ValueError, "public record fields"):
            validate_public_artifact(records)

    def test_private_source_field_rejected(self):
        records = fixture()
        records[0]["sources"][0]["internal_notes"] = "private"
        with self.assertRaisesRegex(ValueError, "public source fields"):
            validate_public_artifact(records)

    def test_unpublished_record_rejected(self):
        records = fixture()
        records[0]["review_status"] = "draft"
        with self.assertRaisesRegex(ValueError, "Unpublished"):
            validate_public_artifact(records)

    def test_duplicate_ids_rejected(self):
        records = fixture()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_public_artifact(records + records)

    def test_unsafe_source_url_rejected(self):
        records = fixture()
        records[0]["sources"][0]["url"] = "javascript:alert(1)"
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            validate_public_artifact(records)

    def test_embedded_url_credentials_rejected(self):
        records = fixture()
        records[0]["sources"][0]["url"] = "https://private:secret@example.org"
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            validate_public_artifact(records)

    def test_documented_claim_needs_primary_source(self):
        records = fixture()
        records[0]["claim_type"] = "documented_event"
        with self.assertRaisesRegex(ValueError, "primary"):
            validate_public_artifact(records)

    def test_invalid_date_rejected(self):
        records = fixture()
        records[0]["sources"][0]["accessed_on"] = "2026-99-99"
        with self.assertRaisesRegex(ValueError, "date"):
            validate_public_artifact(records)

if __name__ == "__main__":
    unittest.main()
