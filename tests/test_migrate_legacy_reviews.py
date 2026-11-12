import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from migrate_legacy_reviews import plan_migration, main
from review_audit_chain import verify_history

def fixture():
    return [{"id":"fictional","title":"Fictional","review_status":"published",
             "internal_review_history":[{"from":"rights_review","to":"approved",
             "reviewer":"Editor One","reason":"Reviewed","timestamp":"2026-11-12T20:00:00Z"}]},
            {"id":"draft","review_status":"draft","internal_review_history":[]}]

class LegacyMigrationTests(unittest.TestCase):
    def test_migrates_without_mutating_source(self):
        data=fixture()
        original=copy.deepcopy(data)
        result,changed=plan_migration(data)
        self.assertEqual(data,original)
        self.assertEqual(changed,["fictional"])
        self.assertEqual(result[0]["review_status"],"published")
        self.assertEqual(result[0]["internal_review_history"][0]["reason"],"Reviewed")
        self.assertEqual(len(verify_history(result[0]["internal_review_history"])),64)
        self.assertEqual(result[1],data[1])

    def test_idempotent_for_sealed_histories(self):
        migrated,_=plan_migration(fixture())
        repeated,changed=plan_migration(migrated)
        self.assertEqual(repeated,migrated)
        self.assertEqual(changed,[])

    def test_missing_published_history_rejected(self):
        data=fixture()
        data[0]["internal_review_history"]=[]
        with self.assertRaisesRegex(ValueError,"lacks review history"):
            plan_migration(data)

    def test_disconnected_history_rejected(self):
        data=fixture()
        data[0]["internal_review_history"].append({"from":"fact_check","to":"rights_review",
            "reviewer":"Editor Two","reason":"Changed","timestamp":"2026-11-12T21:00:00Z"})
        with self.assertRaisesRegex(ValueError,"Disconnected"):
            plan_migration(data)

    def test_duplicate_ids_rejected(self):
        data=fixture()
        data[1]["id"]="fictional"
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            plan_migration(data)

    def test_dry_run_and_create_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            source_dir=root/"source"
            output_dir=root/"vault"
            source_dir.mkdir()
            output_dir.mkdir()
            source=source_dir/"records.json"
            destination=output_dir/"migrated.json"
            receipt_dir=root/"receipts"
            receipt_dir.mkdir()
            receipt=receipt_dir/"receipt.json"
            source.write_text(json.dumps(fixture()))
            original=source.read_bytes()
            main([str(source)])
            self.assertFalse(destination.exists())
            main([str(source),"--confirm-create","--output",str(destination),"--receipt",str(receipt)])
            self.assertEqual(source.read_bytes(),original)
            self.assertEqual(json.loads(destination.read_text())[0]["review_status"],"published")
            with self.assertRaises(FileExistsError):
                main([str(source),"--confirm-create","--output",str(destination)])

if __name__=="__main__":
    unittest.main()
