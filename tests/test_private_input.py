import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from private_input import load_private_json

class PrivateInputTests(unittest.TestCase):
    def test_reads_regular_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "records.json"
            path.write_text('{"test": true}')
            self.assertEqual(load_private_json(path), {"test": True})

    def test_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "records.json"
            path.write_text("[]")
            link = Path(folder) / "link.json"
            link.symlink_to(path)
            with self.assertRaises((OSError, ValueError)):
                load_private_json(link)

    def test_rejects_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises((OSError, ValueError)):
                load_private_json(Path(folder))

    def test_rejects_public_catalogue(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "public-catalogue.json"
            path.write_text("[]")
            with self.assertRaisesRegex(ValueError, "Public catalogue"):
                load_private_json(path)

    def test_invalid_json_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "records.json"
            path.write_text("{invalid")
            with self.assertRaises(json.JSONDecodeError):
                load_private_json(path)

    def test_named_pipe_rejected_without_blocking(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO unsupported")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "pipe"
            os.mkfifo(path)
            with self.assertRaises((OSError, ValueError)):
                load_private_json(path)

if __name__ == "__main__":
    unittest.main()
