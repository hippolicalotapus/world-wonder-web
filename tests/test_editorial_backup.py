import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from editorial_backup import snapshot, verify, write_new, recovery_receipt, restore_pair

NOW = "2026-11-12T22:00:00Z"
def fixture():
    return [{"id": "fictional-test", "title": "Fictional fixture", "collection": "Kindness",
             "summary": "Test data only", "claim_type": "unverified_report",
             "review_status": "draft", "sources": [], "internal_review_history": [
                 {"reviewer": "Test", "reason": "Draft", "timestamp": NOW}]}]

class EditorialBackupTests(unittest.TestCase):
    def test_roundtrip_keeps_private_audit(self):
        records = fixture()
        self.assertEqual(verify(snapshot(records, NOW)), records)

    def test_tampered_backup_is_rejected(self):
        bundle = snapshot(fixture(), NOW)
        bundle["records"][0]["summary"] = "Modified"
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            verify(bundle)

    def test_unknown_format_is_rejected(self):
        bundle = snapshot(fixture(), NOW)
        bundle["format"] = "unknown"
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            verify(bundle)

    def test_invalid_editorial_data_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Invalid editorial"):
            snapshot([{"id": "missing"}], NOW)

    def test_timezone_required(self):
        with self.assertRaises(ValueError):
            snapshot(fixture(), "2026-11-12T22:00:00")

    def test_create_only_permissions(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "backup.json"
            write_new(path, snapshot(fixture(), NOW))
            self.assertEqual(verify(json.loads(path.read_text())), fixture())
            if os.name == "posix":
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                write_new(path, snapshot(fixture(), NOW))

    def test_receipt_links_to_verified_backup_without_private_data(self):
        records = fixture()
        bundle = snapshot(records, NOW)
        receipt = recovery_receipt(bundle, records, NOW)
        self.assertEqual(receipt["backup_sha256"], bundle["sha256"])
        self.assertEqual(receipt["record_count"], 1)
        self.assertNotIn("Fictional fixture", json.dumps(receipt))
        self.assertNotIn("reviewer", json.dumps(receipt))

    def test_receipt_rejects_mismatched_restoration(self):
        records = fixture()
        bundle = snapshot(records, NOW)
        with self.assertRaisesRegex(ValueError, "differ"):
            recovery_receipt(bundle, [], NOW)

    def test_receipt_rejects_tampered_backup(self):
        bundle = snapshot(fixture(), NOW)
        bundle["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            recovery_receipt(bundle, fixture(), NOW)

    def test_receipt_requires_timezone(self):
        with self.assertRaises(ValueError):
            recovery_receipt(snapshot(fixture(), NOW), fixture(), "2026-11-12T22:00:00")

    def test_restore_pair_writes_both_files(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "restored.json"
            receipt = Path(folder) / "receipt.json"
            restore_pair(snapshot(fixture(), NOW), destination, receipt, NOW)
            self.assertEqual(json.loads(destination.read_text()), fixture())
            self.assertEqual(json.loads(receipt.read_text())["record_count"], 1)

    def test_restore_pair_cleans_up_on_receipt_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "restored.json"
            receipt = Path(folder) / "receipt.json"
            def broken_writer(path, payload):
                if path == receipt:
                    raise OSError("simulated receipt write failure")
                write_new(path, payload)
            with self.assertRaisesRegex(OSError, "simulated"):
                restore_pair(snapshot(fixture(), NOW), destination, receipt, NOW, broken_writer)
            self.assertFalse(destination.exists())

    def test_restore_pair_rejects_existing_receipt_without_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "restored.json"
            receipt = Path(folder) / "receipt.json"
            receipt.write_text("existing")
            with self.assertRaises(FileExistsError):
                restore_pair(snapshot(fixture(), NOW), destination, receipt, NOW)
            self.assertFalse(destination.exists())
            self.assertEqual(receipt.read_text(), "existing")

    def test_symlink_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "target.json"
            target.write_text("original")
            link = Path(folder) / "link.json"
            link.symlink_to(target)
            with self.assertRaises(FileExistsError):
                write_new(link, snapshot(fixture(), NOW))
            self.assertEqual(target.read_text(), "original")

if __name__ == "__main__":
    unittest.main()
