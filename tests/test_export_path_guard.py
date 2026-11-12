import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from export_path_guard import validate_export_paths

class ExportPathGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.private = root / "private"
        self.public = root / "public"
        self.private.mkdir()
        self.public.mkdir()
        self.source = self.private / "records.json"
        self.manifest = self.private / "manifest.json"
        self.attestation = self.private / "review.json"
        self.destination = self.public / "public-catalogue.json"
        self.receipt = self.private / "receipt.json"

    def check(self, **overrides):
        values = dict(source=self.source, manifest=self.manifest,
                      attestation=self.attestation, destination=self.destination,
                      receipt=self.receipt)
        values.update(overrides)
        return validate_export_paths(**values)

    def test_valid_separated_paths(self):
        self.assertTrue(self.check())

    def test_private_receipt_cannot_be_public(self):
        with self.assertRaisesRegex(ValueError, "receipt cannot share"):
            self.check(receipt=self.public / "receipt.json")

    def test_private_source_cannot_be_public(self):
        with self.assertRaisesRegex(ValueError, "Private editorial inputs"):
            self.check(source=self.public / "records.json")

    def test_existing_output_rejected(self):
        self.destination.write_text("existing")
        with self.assertRaisesRegex(ValueError, "new files"):
            self.check()
        self.assertEqual(self.destination.read_text(), "existing")

    def test_symlink_output_rejected(self):
        target = self.private / "target"
        target.write_text("keep")
        self.destination.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "new files"):
            self.check()
        self.assertEqual(target.read_text(), "keep")

    def test_duplicate_inputs_rejected(self):
        with self.assertRaisesRegex(ValueError, "distinct"):
            self.check(manifest=self.source)

    def test_receipt_cannot_equal_input(self):
        with self.assertRaisesRegex(ValueError, "distinct"):
            self.check(receipt=self.source)

    def test_missing_parent_rejected(self):
        with self.assertRaisesRegex(ValueError, "existing real"):
            self.check(receipt=self.private / "missing" / "receipt.json")

if __name__ == "__main__":
    unittest.main()
