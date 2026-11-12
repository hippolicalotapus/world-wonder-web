import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from review_audit_chain import seal_history
from review_anchor_guard import authorize_publication_anchors, prepare_anchors

def entry():
    return {"from":"rights_review","to":"approved","reviewer":"Editor One",
            "reason":"Checked","timestamp":"2026-11-12T22:00:00Z"}
def record(status="published", sealed=True):
    return {"id":"fictional","review_status":status,
            "internal_review_history":seal_history([entry()]) if sealed else [entry()]}

class MandatoryAnchorAuthorizationTests(unittest.TestCase):
    def test_sealed_published_requires_anchor(self):
        with self.assertRaisesRegex(ValueError,"required"):
            authorize_publication_anchors([record()])

    def test_matching_anchor_authorizes(self):
        data=[record()]
        self.assertTrue(authorize_publication_anchors(data,prepare_anchors(data)))

    def test_resealed_history_rejected_against_saved_anchor(self):
        data=[record()]
        anchor=prepare_anchors(data)
        data[0]["internal_review_history"]=seal_history([dict(entry(),reason="Altered")])
        with self.assertRaisesRegex(ValueError,"mismatch"):
            authorize_publication_anchors(data,anchor)

    def test_legacy_published_without_anchor_allowed(self):
        self.assertTrue(authorize_publication_anchors([record(sealed=False)]))

    def test_sealed_draft_without_anchor_allowed(self):
        self.assertTrue(authorize_publication_anchors([record(status="draft")]))

    def test_mixed_legacy_and_sealed_published_requires_anchor(self):
        data=[record(sealed=False),dict(record(),id="sealed")]
        with self.assertRaisesRegex(ValueError,"required"):
            authorize_publication_anchors(data)

    def test_malformed_anchor_rejected(self):
        with self.assertRaisesRegex(ValueError,"envelope"):
            authorize_publication_anchors([record(sealed=False)],{"heads":{}})

    def test_unsealed_history_with_explicit_anchor_rejected(self):
        data=[record(sealed=False)]
        with self.assertRaisesRegex(ValueError,"Unsealed"):
            authorize_publication_anchors(data,{"format":"world-wonder-review-anchors-v1","heads":{}})

if __name__=="__main__":
    unittest.main()
