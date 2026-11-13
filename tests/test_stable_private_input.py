import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from stable_private_input import read_stable, assert_unchanged
from verify_migration import main as verify_main
from recover_migration_receipt import recover_receipt
from migrate_legacy_reviews import plan_migration
from migration_receipt import make_receipt

def fixture():
    return [{"id":"fixture","review_status":"published","internal_review_history":[
        {"from":"rights_review","to":"approved","reviewer":"Editor One","reason":"Reviewed",
         "timestamp":"2026-11-12T20:00:00Z"}]}]

class StableInputTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        for name in ("source","migrated","receipt"):
            (root/name).mkdir()
        self.source=root/"source"/"records.json"
        self.migrated=root/"migrated"/"records.json"
        self.receipt=root/"receipt"/"receipt.json"
        self.original=fixture()
        self.output,_=plan_migration(self.original)
        self.source.write_text(json.dumps(self.original))
        self.migrated.write_text(json.dumps(self.output))

    def test_stable_read_and_check(self):
        data,stamp=read_stable(self.source)
        assert_unchanged(self.source,stamp,data)

    def test_changed_file_detected(self):
        data,stamp=read_stable(self.source)
        self.source.write_text(json.dumps(dict(changed=True)))
        with self.assertRaisesRegex(ValueError,"changed"):
            assert_unchanged(self.source,stamp,data)

    def test_replaced_inode_detected(self):
        data,stamp=read_stable(self.source)
        replacement=self.source.with_suffix(".new")
        replacement.write_text(json.dumps(self.original))
        replacement.replace(self.source)
        with self.assertRaisesRegex(ValueError,"changed"):
            assert_unchanged(self.source,stamp,data)

    def test_symlink_refused(self):
        alias=self.source.with_name("alias.json")
        alias.symlink_to(self.source)
        with self.assertRaisesRegex(ValueError,"symlink"):
            read_stable(alias)

    def test_recovery_rejects_midflight_edit(self):
        from private_file_locks import locked_inputs
        with self.assertRaisesRegex(ValueError,"changed"):
            with locked_inputs((self.source,self.migrated)) as reader:
                reader.read_json(self.source)
                self.source.write_text("{}")
                reader.read_json(self.source)
        self.assertFalse(self.receipt.exists())

    def test_verifier_detects_midflight_edit(self):
        from private_file_locks import locked_inputs
        self.receipt.write_text(json.dumps(make_receipt(self.original,self.output)))
        with self.assertRaisesRegex(ValueError,"changed"):
            with locked_inputs((self.source,self.migrated,self.receipt)) as reader:
                reader.read_json(self.source)
                self.source.write_text("{}")
                reader.read_json(self.source)

if __name__=="__main__":
    unittest.main()
