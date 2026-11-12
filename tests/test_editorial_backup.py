import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from editorial_backup import snapshot, verify, write_new

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
