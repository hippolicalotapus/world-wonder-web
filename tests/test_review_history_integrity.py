import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from review_history_guard import check_history
from publication_manifest import prepare
from independent_review import make_attestation

NOW="2026-11-12T23:00:00Z"
def history():
    return [
        {"from":"rights_review","to":"approved","reviewer":"Editor One","reason":"Verified","timestamp":"2026-11-12T21:00:00Z"},
        {"from":"approved","to":"published","reviewer":"Editor One","reason":"Released","timestamp":"2026-11-12T22:00:00Z"}
    ]
def record():
    return [{"id":"fixture","title":"Fixture","collection":"Kindness","summary":"Fictional",
             "claim_type":"unverified_report","review_status":"published",
             "sources":[{"title":"Example","url":"https://example.org","publisher":"Example",
                         "accessed_on":"2026-11-12","source_type":"secondary","rights_status":"link_only"}],
             "internal_review_history":history()}]

class ReviewHistoryIntegrityTests(unittest.TestCase):
    def test_coherent_history(self):
        self.assertEqual(check_history(history(),__import__("datetime").datetime.fromisoformat(NOW.replace("Z","+00:00"))),{"editor one"})

    def test_disconnected_history_blocks_attestation(self):
        records=record()
        records[0]["internal_review_history"][1]["from"]="fact_check"
        with self.assertRaisesRegex(ValueError,"(Disconnected|transition)"):
            make_attestation(records,prepare(records),"Editor Two",NOW)

    def test_reversed_timestamps_block_attestation(self):
        records=record()
        records[0]["internal_review_history"][1]["timestamp"]="2026-11-12T20:00:00Z"
        with self.assertRaisesRegex(ValueError,"out of order"):
            make_attestation(records,prepare(records),"Editor Two",NOW)

    def test_missing_reason_blocks_attestation(self):
        records=record()
        records[0]["internal_review_history"][0]["reason"]=""
        with self.assertRaisesRegex(ValueError,"reason"):
            make_attestation(records,prepare(records),"Editor Two",NOW)

    def test_illegal_transition_blocks_attestation(self):
        records=record()
        records[0]["internal_review_history"][0]["to"]="draft"
        with self.assertRaisesRegex(ValueError,"transition"):
            make_attestation(records,prepare(records),"Editor Two",NOW)

    def test_valid_history_allows_attestation(self):
        records=record()
        self.assertEqual(make_attestation(records,prepare(records),"Editor Two",NOW)["decision"],"approved")

if __name__=="__main__":
    unittest.main()
