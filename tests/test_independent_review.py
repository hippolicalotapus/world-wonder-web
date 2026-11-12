import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from publication_manifest import prepare
from independent_review import make_attestation, validate_attestation

NOW = "2026-11-12T22:00:00Z"
def fixture():
    return [{"id": "fictional", "title": "Fictional", "collection": "Kindness",
             "summary": "Fixture", "claim_type": "unverified_report",
             "review_status": "published",
             "sources": [{"title": "Example", "url": "https://example.org",
                          "publisher": "Example", "accessed_on": "2026-11-12",
                          "source_type": "secondary", "rights_status": "link_only"}],
             "internal_review_history": [
                 {"from": "rights_review", "to": "approved", "reviewer": "Editor One",
                  "reason": "Checked", "timestamp": NOW},
                 {"from": "approved", "to": "published", "reviewer": "Editor One",
                  "reason": "Approved", "timestamp": NOW}]}]

class IndependentReviewTests(unittest.TestCase):
    def test_independent_approval(self):
        records = fixture()
        manifest = prepare(records)
        receipt = make_attestation(records, manifest, "Editor Two", NOW)
        self.assertTrue(validate_attestation(records, manifest, receipt))

    def test_same_reviewer_blocked(self):
        records = fixture()
        with self.assertRaisesRegex(ValueError, "must differ"):
            make_attestation(records, prepare(records), "editor one", NOW)

    def test_missing_editorial_history_blocked(self):
        records = fixture()
        records[0].pop("internal_review_history")
        with self.assertRaisesRegex(ValueError, "lacks recorded"):
            make_attestation(records, prepare(records), "Editor Two", NOW)

    def test_source_change_invalidates_attestation(self):
        records = fixture()
        manifest = prepare(records)
        receipt = make_attestation(records, manifest, "Editor Two", NOW)
        records[0]["summary"] = "Changed"
        with self.assertRaisesRegex(ValueError, "source changed"):
            validate_attestation(records, manifest, receipt)

    def test_attestation_tampering_blocked(self):
        records = fixture()
        manifest = prepare(records)
        receipt = make_attestation(records, manifest, "Editor Two", NOW)
        receipt["decision"] = "rejected"
        with self.assertRaisesRegex(ValueError, "Invalid"):
            validate_attestation(records, manifest, receipt)

if __name__ == "__main__":
    unittest.main()
