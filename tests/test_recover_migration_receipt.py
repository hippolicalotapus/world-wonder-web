import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from migrate_legacy_reviews import plan_migration
from migration_receipt import verify_receipt
from recover_migration_receipt import recover_receipt, main

def records():
    return [{"id":"fictional","review_status":"published","internal_review_history":[
        {"from":"rights_review","to":"approved","reviewer":"Editor One","reason":"Reviewed",
         "timestamp":"2026-11-12T20:00:00Z"}]}]

class MissingReceiptRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        for name in ("source","migrated","receipts"):
            (root/name).mkdir()
        self.original=root/"source"/"original.json"
        self.migrated=root/"migrated"/"migrated.json"
        self.receipt=root/"receipts"/"receipt.json"
        self.source=records()
        self.output,_=plan_migration(self.source)
        self.original.write_text(json.dumps(self.source))
        self.migrated.write_text(json.dumps(self.output))

    def test_recovers_only_receipt(self):
        before=(self.original.read_bytes(),self.migrated.read_bytes())
        proof=recover_receipt(self.original,self.migrated,self.receipt)
        self.assertTrue(verify_receipt(self.source,self.output,proof))
        self.assertEqual(before,(self.original.read_bytes(),self.migrated.read_bytes()))

    def test_requires_explicit_confirmation(self):
        with self.assertRaises(SystemExit):
            main([str(self.original),str(self.migrated),str(self.receipt)])
        self.assertFalse(self.receipt.exists())

    def test_refuses_overwrite(self):
        recover_receipt(self.original,self.migrated,self.receipt)
        original=self.receipt.read_bytes()
        with self.assertRaises(ValueError):
            recover_receipt(self.original,self.migrated,self.receipt)
        self.assertEqual(self.receipt.read_bytes(),original)

    def test_refuses_invalid_migrated_copy(self):
        self.output[0]["internal_review_history"][0]["reason"]="Changed"
        self.migrated.write_text(json.dumps(self.output))
        with self.assertRaises(ValueError):
            recover_receipt(self.original,self.migrated,self.receipt)
        self.assertFalse(self.receipt.exists())

    def test_refuses_same_directory(self):
        with self.assertRaisesRegex(ValueError,"separate"):
            recover_receipt(self.original,self.migrated,self.migrated.parent/"receipt.json")

    def test_refuses_symlink_migrated_file(self):
        self.migrated.unlink()
        self.migrated.symlink_to(self.original)
        with self.assertRaises((OSError,ValueError)):
            recover_receipt(self.original,self.migrated,self.receipt)

    def test_refuses_orphaned_receipt(self):
        self.migrated.unlink()
        self.receipt.write_text("{}")
        with self.assertRaises(ValueError):
            recover_receipt(self.original,self.migrated,self.receipt)

if __name__=="__main__":
    unittest.main()
