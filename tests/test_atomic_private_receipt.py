import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from atomic_private_receipt import write_new_receipt

class AtomicReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.vault=self.root/"vault"
        self.vault.mkdir()
        self.target=self.vault/"receipt.json"

    def test_create_and_permissions(self):
        write_new_receipt(self.target,{"format":"test","count":1})
        self.assertEqual(json.loads(self.target.read_text()),{"format":"test","count":1})
        self.assertEqual(self.target.stat().st_mode & 0o777,0o600)
        self.assertEqual(sorted(p.name for p in self.vault.iterdir()),["receipt.json"])

    def test_no_overwrite(self):
        self.target.write_text("original")
        with self.assertRaises(FileExistsError):
            write_new_receipt(self.target,{"count":2})
        self.assertEqual(self.target.read_text(),"original")
        self.assertEqual(sorted(p.name for p in self.vault.iterdir()),["receipt.json"])

    def test_symlink_destination_not_followed(self):
        other=self.root/"other.json"
        other.write_text("private")
        self.target.symlink_to(other)
        with self.assertRaises(FileExistsError):
            write_new_receipt(self.target,{"count":2})
        self.assertEqual(other.read_text(),"private")

    def test_symlink_directory_rejected(self):
        alias=self.root/"alias"
        alias.symlink_to(self.vault,target_is_directory=True)
        with self.assertRaises((OSError,ValueError)):
            write_new_receipt(alias/"receipt.json",{"count":1})
        self.assertFalse(self.target.exists())

    def test_public_catalogue_name_rejected(self):
        with self.assertRaisesRegex(ValueError,"Invalid"):
            write_new_receipt(self.vault/"public-catalogue.json",{})

    def test_missing_directory_rejected(self):
        with self.assertRaises(OSError):
            write_new_receipt(self.root/"missing"/"receipt.json",{})

if __name__=="__main__":
    unittest.main()
