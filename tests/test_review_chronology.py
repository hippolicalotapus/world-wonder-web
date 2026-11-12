import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from publication_manifest import prepare
from independent_review import make_attestation

NOW = "2026-11-12T23:00:00Z"
def fixture():
    return [{"id":"fictional","title":"Fictional","collection":"Kindness",
             "summary":"Synthetic fixture","claim_type":"unverified_report",
             "review_status":"published",
             "sources":[{"title":"Example","url":"https://example.org","publisher":"Example",
                         "accessed_on":"2026-11-12","source_type":"secondary","rights_status":"link_only"}],
             "internal_review_history":[{"from":"rights_review","to":"approved",
                                          "reviewer":"Editor One","reason":"Reviewed",
                                          "timestamp":"2026-11-12T22:00:00Z"}]}]

class ReviewChronologyTests(unittest.TestCase):
    def test_valid_later_independent_review(self):
        records=fixture()
        self.assertEqual(make_attestation(records,prepare(records),"Editor Two",NOW)["decision"],"approved")

    def test_review_cannot_precede_editorial_approval(self):
        records=fixture()
        with self.assertRaisesRegex(ValueError,"predates"):
            make_attestation(records,prepare(records),"Editor Two","2026-11-12T21:00:00Z")

    def test_blank_editorial_approver_rejected(self):
        records=fixture()
        records[0]["internal_review_history"][0]["reviewer"]=" "
        with self.assertRaisesRegex(ValueError,"Invalid editorial approval entry"):
            make_attestation(records,prepare(records),"Editor Two",NOW)

    def test_naive_editorial_approval_timestamp_rejected(self):
        records=fixture()
        records[0]["internal_review_history"][0]["timestamp"]="2026-11-12T22:00:00"
        with self.assertRaisesRegex(ValueError,"Invalid editorial approval timestamp"):
            make_attestation(records,prepare(records),"Editor Two",NOW)

    def test_invalid_review_history_entry_rejected(self):
        records=fixture()
        records[0]["internal_review_history"].append(None)
        with self.assertRaisesRegex(ValueError,"Invalid review history entry"):
            make_attestation(records,prepare(records),"Editor Two",NOW)

    def test_same_editor_still_blocked(self):
        records=fixture()
        with self.assertRaisesRegex(ValueError,"must differ"):
            make_attestation(records,prepare(records),"editor one",NOW)

if __name__ == "__main__":
    unittest.main()
