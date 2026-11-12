import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from migrate_legacy_reviews import plan_migration, main as migrate
from migration_receipt import make_receipt, verify_receipt
from verify_migration import main as verify

def fixture():
    return [{"id":"fictional","review_status":"published","internal_review_history":[
        {"from":"rights_review","to":"approved","reviewer":"Editor One","reason":"Reviewed",
         "timestamp":"2026-11-12T20:00:00Z"}]}]

class MigrationReceiptTests(unittest.TestCase):
    def test_receipt_has_only_privacy_minimal_fields(self):
        original=fixture()
        migrated,_=plan_migration(original)
        receipt=make_receipt(original,migrated)
        self.assertEqual(set(receipt),{"format","source_sha256","migrated_sha256","record_count","migrated_count"})
        self.assertNotIn("Editor One",str(receipt))
        self.assertTrue(verify_receipt(original,migrated,receipt))

    def test_tampered_migrated_record_rejected(self):
        original=fixture()
        migrated,_=plan_migration(original)
        receipt=make_receipt(original,migrated)
        migrated[0]["internal_review_history"][0]["reason"]="Altered"
        with self.assertRaises(ValueError):
            verify_receipt(original,migrated,receipt)

    def test_extra_private_field_in_receipt_rejected(self):
        original=fixture()
        migrated,_=plan_migration(original)
        receipt=make_receipt(original,migrated)
        receipt["reviewer_email"]="secret@example.org"
        with self.assertRaisesRegex(ValueError,"Invalid migration receipt"):
            verify_receipt(original,migrated,receipt)

    def test_malformed_hash_rejected(self):
        original=fixture()
        migrated,_=plan_migration(original)
        receipt=make_receipt(original,migrated)
        receipt["source_sha256"]="invalid"
        with self.assertRaisesRegex(ValueError,"hashes"):
            verify_receipt(original,migrated,receipt)

    def test_read_only_verification_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for name in ("source","migrated","receipts"):
                (root/name).mkdir()
            source=root/"source"/"records.json"
            target=root/"migrated"/"migrated.json"
            receipt=root/"receipts"/"receipt.json"
            source.write_text(json.dumps(fixture()))
            before=source.read_bytes()
            migrate([str(source),"--confirm-create","--output",str(target),"--receipt",str(receipt)])
            files_before=(source.read_bytes(),target.read_bytes(),receipt.read_bytes())
            self.assertEqual(verify([str(source),str(target),str(receipt)]),0)
            self.assertEqual(files_before,(source.read_bytes(),target.read_bytes(),receipt.read_bytes()))
            self.assertEqual(source.read_bytes(),before)
            with self.assertRaises(FileExistsError):
                migrate([str(source),"--confirm-create","--output",str(target),"--receipt",str(receipt)])

    def test_missing_receipt_path_blocks_creation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"source").mkdir()
            (root/"output").mkdir()
            source=root/"source"/"records.json"
            target=root/"output"/"migrated.json"
            source.write_text(json.dumps(fixture()))
            with self.assertRaisesRegex(ValueError,"receipt path required"):
                migrate([str(source),"--confirm-create","--output",str(target)])
            self.assertFalse(target.exists())

if __name__=="__main__":
    unittest.main()
