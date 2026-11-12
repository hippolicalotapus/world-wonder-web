import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from editorial_workflow import transition
from export_public_catalogue import export

NOW = "2026-11-12T22:00:00Z"

def sample():
    return {
        "id": "test-example", "title": "Test example", "collection": "Kindness",
        "summary": "Fictional fixture", "claim_type": "documented_event",
        "review_status": "draft",
        "sources": [{"title": "Example", "url": "https://example.org/record",
                     "publisher": "Example", "accessed_on": "2026-11-12",
                     "source_type": "primary", "rights_status": "link_only"}],
        "private_evidence": "RESTRICTED"
    }

class EditorialWorkflowTests(unittest.TestCase):
    def test_full_review_path_requires_private_field_removal(self):
        item = sample()
        for status in ("fact_check", "rights_review"):
            item = transition(item, status, "Reviewer", "Checked", NOW)
        with self.assertRaisesRegex(ValueError, "Publication gates"):
            transition(item, "approved", "Reviewer", "Approved", NOW)
        item.pop("private_evidence")
        item = transition(item, "approved", "Reviewer", "Approved", NOW)
        item = transition(item, "published", "Reviewer", "Published", NOW)
        self.assertEqual(len(item["internal_review_history"]), 4)
        self.assertNotIn("internal_review_history", export([item])[0])

    def test_no_shortcut_from_draft_to_published(self):
        with self.assertRaisesRegex(ValueError, "Invalid editorial transition"):
            transition(sample(), "published", "Reviewer", "Skip", NOW)

    def test_reviewer_reason_and_timezone_required(self):
        for reviewer, reason, when in [("", "OK", NOW), ("Reviewer", "", NOW), ("Reviewer", "OK", "2026-11-12T22:00:00")]:
            with self.assertRaises(ValueError):
                transition(sample(), "fact_check", reviewer, reason, when)

    def test_rejection_and_return_to_draft(self):
        item = transition(sample(), "rejected", "Reviewer", "Insufficient evidence", NOW)
        self.assertEqual(item["review_status"], "rejected")
        self.assertEqual(transition(item, "draft", "Reviewer", "Revise", NOW)["review_status"], "draft")

    def test_pending_rights_blocks_approval(self):
        item = sample()
        item.pop("private_evidence")
        item["sources"][0]["rights_status"] = "permission_pending"
        for state in ("fact_check", "rights_review"):
            item = transition(item, state, "Reviewer", "Checked", NOW)
        with self.assertRaisesRegex(ValueError, "Publication gates"):
            transition(item, "approved", "Reviewer", "Approved", NOW)

    def test_history_is_immutable_on_failed_transition(self):
        item = sample()
        with self.assertRaises(ValueError):
            transition(item, "published", "Reviewer", "Invalid", NOW)
        self.assertNotIn("internal_review_history", item)

if __name__ == "__main__":
    unittest.main()
