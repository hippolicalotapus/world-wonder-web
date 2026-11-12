import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from review_audit_chain import seal_history, verify_history
from review_history_guard import check_history
from datetime import datetime

NOW = datetime.fromisoformat("2026-11-12T23:00:00+00:00")
def history():
    return [{"from":"rights_review","to":"approved","reviewer":"Editor One",
             "reason":"Reviewed","timestamp":"2026-11-12T21:00:00Z"},
            {"from":"approved","to":"published","reviewer":"Editor One",
             "reason":"Published","timestamp":"2026-11-12T22:00:00Z"}]

class ReviewAuditChainTests(unittest.TestCase):
    def test_sealed_history_passes_publication_guard(self):
        sealed = seal_history(history())
        self.assertEqual(check_history(sealed, NOW), {"editor one"})
        self.assertEqual(len(verify_history(sealed)), 64)

    def test_changed_reason_rejected(self):
        sealed = seal_history(history())
        sealed[0]["reason"] = "Altered"
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            check_history(sealed, NOW)

    def test_deleted_middle_link_rejected(self):
        sealed = seal_history(history())
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            verify_history(sealed[1:])

    def test_reordered_history_rejected(self):
        sealed = seal_history(history())
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            verify_history(list(reversed(sealed)))

    def test_trusted_anchor_rejects_resealed_rewrite(self):
        sealed = seal_history(history())
        trusted = verify_history(sealed)
        altered = history()
        altered[0]["reason"] = "Changed and resealed"
        with self.assertRaisesRegex(ValueError, "trusted anchor"):
            verify_history(seal_history(altered), trusted)

    def test_legacy_history_remains_compatible(self):
        self.assertEqual(check_history(history(), NOW), {"editor one"})

    def test_mixed_history_rejected(self):
        mixed = seal_history(history())
        mixed[1] = history()[1]
        with self.assertRaisesRegex(ValueError, "Unsealed"):
            check_history(mixed, NOW)

if __name__ == "__main__":
    unittest.main()
