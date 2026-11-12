import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from review_audit_chain import seal_history
from review_anchor_guard import prepare_anchors, verify_anchors

def records():
    history=[{"from":"rights_review","to":"approved","reviewer":"Editor One",
              "reason":"Checked","timestamp":"2026-11-12T20:00:00Z"}]
    return [{"id":"fixture","review_status":"published",
             "internal_review_history":seal_history(history)}]

class ReviewAnchorGuardTests(unittest.TestCase):
    def test_matching_anchor_passes(self):
        data=records()
        self.assertTrue(verify_anchors(data,prepare_anchors(data)))

    def test_resealed_rewrite_rejected(self):
        data=records()
        anchors=prepare_anchors(data)
        data[0]["internal_review_history"][0]["reason"]="Changed"
        changed=[{k:v for k,v in data[0]["internal_review_history"][0].items()
                  if k not in ("entry_hash","previous_hash")}]
        data[0]["internal_review_history"]=seal_history(changed)
        with self.assertRaisesRegex(ValueError,"Trusted audit anchor mismatch"):
            verify_anchors(data,anchors)

    def test_missing_published_anchor_rejected(self):
        data=records()
        with self.assertRaisesRegex(ValueError,"Trusted audit anchor mismatch"):
            verify_anchors(data,{"format":"world-wonder-review-anchors-v1","heads":{}})

    def test_unsealed_published_history_rejected(self):
        data=records()
        data[0]["internal_review_history"][0].pop("entry_hash")
        with self.assertRaisesRegex(ValueError,"Unsealed"):
            prepare_anchors(data)

    def test_duplicate_record_ids_rejected(self):
        data=records()
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            prepare_anchors(data+data)

    def test_invalid_anchor_envelope_rejected(self):
        data=records()
        anchors=prepare_anchors(data)
        anchors["private_email"]="secret@example.org"
        with self.assertRaisesRegex(ValueError,"Invalid trusted anchor envelope"):
            verify_anchors(data,anchors)

    def test_malformed_sha256_anchor_rejected(self):
        data=records()
        anchors=prepare_anchors(data)
        anchors["heads"]["fixture"]="NOT-A-SHA256"
        with self.assertRaisesRegex(ValueError,"Invalid trusted anchor heads"):
            verify_anchors(data,anchors)

    def test_blank_anchor_record_id_rejected(self):
        data=records()
        anchors=prepare_anchors(data)
        anchors["heads"][" "]=anchors["heads"].pop("fixture")
        with self.assertRaisesRegex(ValueError,"Invalid trusted anchor heads"):
            verify_anchors(data,anchors)

    def test_legacy_unsealed_draft_allowed_without_anchor(self):
        data=[{"id":"draft","review_status":"draft","internal_review_history":[]}]
        self.assertTrue(verify_anchors(data,prepare_anchors(data)))

if __name__=="__main__":
    unittest.main()
