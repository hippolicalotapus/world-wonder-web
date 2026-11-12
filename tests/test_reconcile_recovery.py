import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from editorial_backup import snapshot, recovery_receipt
from reconcile_recovery import reconcile

NOW = "2026-11-12T22:00:00Z"
def fixture():
    return [{"id": "fictional", "title": "Test", "collection": "Kindness",
             "summary": "Fictional only", "claim_type": "unverified_report",
             "review_status": "draft", "sources": []}]

class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.records = fixture()
        self.bundle = snapshot(self.records, NOW)
        self.receipt = recovery_receipt(self.bundle, self.records, NOW)

    def test_complete_pair_verified(self):
        self.assertEqual(reconcile(self.bundle, self.records, self.receipt), "verified")

    def test_not_started(self):
        self.assertEqual(reconcile(self.bundle, None, None), "not_started")

    def test_missing_receipt(self):
        self.assertEqual(reconcile(self.bundle, self.records, None), "missing_receipt")

    def test_missing_restored_file(self):
        self.assertEqual(reconcile(self.bundle, None, self.receipt), "missing_restored_records")

    def test_changed_restored_data(self):
        self.assertEqual(reconcile(self.bundle, [], self.receipt), "restored_data_mismatch")

    def test_tampered_backup(self):
        self.bundle["sha256"] = "0" * 64
        self.assertEqual(reconcile(self.bundle, self.records, self.receipt), "invalid_backup")

    def test_wrong_receipt_hash(self):
        self.receipt["backup_sha256"] = "0" * 64
        self.assertEqual(reconcile(self.bundle, self.records, self.receipt), "receipt_mismatch")

    def test_receipt_extra_private_field(self):
        self.receipt["reviewer_email"] = "private@example.org"
        self.assertEqual(reconcile(self.bundle, self.records, self.receipt), "invalid_receipt")

    def test_receipt_bad_timestamp(self):
        self.receipt["restored_at"] = "not-a-date"
        self.assertEqual(reconcile(self.bundle, self.records, self.receipt), "invalid_receipt")

if __name__ == "__main__":
    unittest.main()
