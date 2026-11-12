import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from review_console import review_records, safe_write, file_digest

NOW = "2026-11-12T22:00:00Z"
def record():
    return {"id": "fixture", "title": "Fictional test", "collection": "Kindness",
            "summary": "Not a published article", "claim_type": "unverified_report",
            "review_status": "draft", "sources": [], "private_evidence": "PRIVATE"}

class ReviewConsoleTests(unittest.TestCase):
    def test_decision_preserves_original_and_private_audit(self):
        original = [record()]
        result = review_records(original, "fixture", "fact_check", "Editor", "Investigate", NOW)
        self.assertEqual(original[0]["review_status"], "draft")
        self.assertEqual(result[0]["review_status"], "fact_check")
        self.assertEqual(result[0]["internal_review_history"][0]["reviewer"], "Editor")
        self.assertEqual(result[0]["private_evidence"], "PRIVATE")

    def test_duplicate_ids_blocked(self):
        with self.assertRaisesRegex(ValueError, "exactly one"):
            review_records([record(), record()], "fixture", "fact_check", "Editor", "Check", NOW)

    def test_unknown_record_blocked(self):
        with self.assertRaises(ValueError):
            review_records([record()], "unknown", "fact_check", "Editor", "Check", NOW)

    def test_premature_publication_blocked(self):
        with self.assertRaises(ValueError):
            review_records([record()], "fixture", "published", "Editor", "Skip", NOW)

    def test_safe_write_private_permissions_and_valid_json(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "private.json"
            safe_write(output, [record()])
            self.assertEqual(json.loads(output.read_text())[0]["id"], "fixture")
            if os.name == "posix":
                self.assertEqual(output.stat().st_mode & 0o777, 0o600)

    def test_expected_status_prevents_stale_review(self):
        with self.assertRaisesRegex(ValueError, "Stale review"):
            review_records([record()], "fixture", "fact_check", "Editor", "Check", NOW, "approved")

    def test_safe_write_refuses_existing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "review.json"
            safe_write(output, [record()])
            original = output.read_bytes()
            with self.assertRaises(FileExistsError):
                safe_write(output, [])
            self.assertEqual(output.read_bytes(), original)

    def test_file_digest_detects_source_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "source.json"
            output.write_text("[]")
            before = file_digest(output)
            output.write_text("[1]")
            self.assertNotEqual(before, file_digest(output))

    def test_safe_write_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "target.json"
            target.write_text("[]")
            link = Path(folder) / "link.json"
            link.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "symlink"):
                safe_write(link, [record()])
            self.assertEqual(target.read_text(), "[]")

if __name__ == "__main__":
    unittest.main()
