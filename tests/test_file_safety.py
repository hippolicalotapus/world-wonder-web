import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from editorial_backup import write_new, remove_if_unchanged, snapshot, restore_pair

NOW = "2026-11-12T22:00:00Z"
def fixture():
    return [{"id": "fictional-test", "title": "Fictional fixture",
             "collection": "Kindness", "summary": "Test",
             "claim_type": "unverified_report", "review_status": "draft", "sources": []}]

class FileSafetyTests(unittest.TestCase):
    def test_cleanup_removes_only_original_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "new.json"
            write_new(path, [])
            stat = path.lstat()
            self.assertTrue(remove_if_unchanged(path, (stat.st_dev, stat.st_ino)))
            self.assertFalse(path.exists())

    def test_cleanup_preserves_replaced_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "new.json"
            write_new(path, [])
            stat = path.lstat()
            replacement = Path(folder) / "replacement"
            replacement.write_text("replacement")
            os.replace(replacement, path)
            self.assertFalse(remove_if_unchanged(path, (stat.st_dev, stat.st_ino)))
            self.assertEqual(path.read_text(), "replacement")

    def test_restore_receipt_failure_preserves_replacement(self):
        with tempfile.TemporaryDirectory() as folder:
            restored = Path(folder) / "restored.json"
            receipt = Path(folder) / "receipt.json"
            def writer(path, payload):
                if path == receipt:
                    replacement = Path(folder) / "other.json"
                    replacement.write_text("another writer")
                    os.replace(replacement, restored)
                    raise OSError("simulated interruption")
                write_new(path, payload)
            with self.assertRaisesRegex(OSError, "interruption"):
                restore_pair(snapshot(fixture(), NOW), restored, receipt, NOW, writer)
            self.assertEqual(restored.read_text(), "another writer")

    def test_existing_destination_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "existing.json"
            path.write_text("keep")
            with self.assertRaises(FileExistsError):
                write_new(path, {"secret": "not written"})
            self.assertEqual(path.read_text(), "keep")

if __name__ == "__main__":
    unittest.main()
