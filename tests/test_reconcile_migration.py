import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from migrate_legacy_reviews import plan_migration
from migration_receipt import make_receipt
from reconcile_migration import reconcile, main

def fixture():
    return [{"id":"fixture","review_status":"published","internal_review_history":[
        {"from":"rights_review","to":"approved","reviewer":"Editor One",
         "reason":"Reviewed","timestamp":"2026-11-12T20:00:00Z"}]}]

class InterruptedMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name)
        self.original=root/"original"/"records.json"
        self.migrated=root/"migrated"/"records.json"
        self.receipt=root/"receipts"/"receipt.json"
        for path in (self.original,self.migrated,self.receipt):
            path.parent.mkdir()
        self.records=fixture()
        self.original.write_text(json.dumps(self.records))
        self.output,_=plan_migration(self.records)

    def test_not_started(self):
        before=self.original.read_bytes()
        self.assertEqual(reconcile(self.original,self.migrated,self.receipt),"not_started")
        self.assertEqual(before,self.original.read_bytes())

    def test_missing_receipt_recognizes_valid_output(self):
        self.migrated.write_text(json.dumps(self.output))
        before=self.migrated.read_bytes()
        self.assertEqual(reconcile(self.original,self.migrated,self.receipt),"missing_receipt")
        self.assertEqual(before,self.migrated.read_bytes())
        self.assertFalse(self.receipt.exists())
        self.assertEqual(main([str(self.original),str(self.migrated),str(self.receipt)]),2)

    def test_orphaned_receipt(self):
        self.receipt.write_text(json.dumps(make_receipt(self.records,self.output)))
        self.assertEqual(reconcile(self.original,self.migrated,self.receipt),"orphaned_receipt")

    def test_complete_pair_verified(self):
        self.migrated.write_text(json.dumps(self.output))
        self.receipt.write_text(json.dumps(make_receipt(self.records,self.output)))
        before=(self.original.read_bytes(),self.migrated.read_bytes(),self.receipt.read_bytes())
        self.assertEqual(reconcile(self.original,self.migrated,self.receipt),"verified_complete")
        self.assertEqual(before,(self.original.read_bytes(),self.migrated.read_bytes(),self.receipt.read_bytes()))

    def test_tampered_output_without_receipt_rejected(self):
        self.output[0]["internal_review_history"][0]["reason"]="tampered"
        self.migrated.write_text(json.dumps(self.output))
        with self.assertRaises(ValueError):
            reconcile(self.original,self.migrated,self.receipt)

    def test_tampered_receipt_rejected(self):
        self.migrated.write_text(json.dumps(self.output))
        receipt=make_receipt(self.records,self.output)
        receipt["migrated_sha256"]="0"*64
        self.receipt.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError,"mismatch"):
            reconcile(self.original,self.migrated,self.receipt)

    def test_symlink_output_rejected(self):
        self.migrated.symlink_to(self.original)
        with self.assertRaises((OSError,ValueError)):
            reconcile(self.original,self.migrated,self.receipt)

    def test_reject_same_path(self):
        with self.assertRaisesRegex(ValueError,"distinct"):
            reconcile(self.original,self.original,self.receipt)

if __name__=="__main__":
    unittest.main()
