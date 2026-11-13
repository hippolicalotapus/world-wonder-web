import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from private_file_locks import locked_inputs
from migrate_legacy_reviews import plan_migration
from migration_receipt import make_receipt
from recover_migration_receipt import recover_receipt
from verify_migration import main as verify_main

def fixture():
    return [{"id":"fixture","review_status":"published","internal_review_history":[
        {"from":"rights_review","to":"approved","reviewer":"Editor One","reason":"Reviewed",
         "timestamp":"2026-11-12T20:00:00Z"}]}]

class PrivateLockTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        for name in ("source","migrated","receipts"):
            (root/name).mkdir()
        self.source=root/"source"/"source.json"
        self.migrated=root/"migrated"/"migrated.json"
        self.receipt=root/"receipts"/"receipt.json"
        self.records=fixture()
        self.output,_=plan_migration(self.records)
        self.source.write_text(json.dumps(self.records))
        self.migrated.write_text(json.dumps(self.output))

    def test_locked_read_only_inputs(self):
        with locked_inputs((self.source,self.migrated)):
            self.assertTrue(self.source.exists())

    def test_descriptor_read_returns_private_json(self):
        with locked_inputs((self.source,)) as reader:
            self.assertEqual(reader.read_json(self.source), self.records)

    def test_descriptor_read_refuses_unlocked_path(self):
        with locked_inputs((self.source,)) as reader:
            with self.assertRaisesRegex(ValueError, "not held"):
                reader.read_json(self.migrated)

    def test_descriptor_read_detects_mutation(self):
        with self.assertRaisesRegex(ValueError, "changed"):
            with locked_inputs((self.source,)) as reader:
                self.source.write_text("{}")
                reader.read_json(self.source)

    def test_duplicate_paths_rejected(self):
        with self.assertRaisesRegex(ValueError,"distinct"):
            with locked_inputs((self.source,self.source)):
                pass

    def test_symlink_rejected(self):
        alias=self.source.parent/"alias.json"
        alias.symlink_to(self.source)
        with self.assertRaises((OSError,ValueError)):
            with locked_inputs((alias,)):
                pass

    def test_replaced_file_detected(self):
        with self.assertRaisesRegex(ValueError,"changed"):
            with locked_inputs((self.source,)):
                replacement=self.source.with_suffix(".new")
                replacement.write_text(self.source.read_text())
                replacement.replace(self.source)

    def test_modified_file_detected(self):
        with self.assertRaisesRegex(ValueError,"changed"):
            with locked_inputs((self.source,)):
                self.source.write_text("{}")

    def test_directory_replacement_detected(self):
        with self.assertRaisesRegex(ValueError,"directory changed"):
            with locked_inputs((self.source,)):
                original_dir=self.source.parent
                moved=original_dir.with_name("source-moved")
                original_dir.rename(moved)
                original_dir.mkdir()
                (original_dir/self.source.name).write_text("{}")

    def test_directory_symlink_rejected(self):
        alias=self.source.parent.with_name("source-alias")
        alias.symlink_to(self.source.parent,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,"directory symlink"):
            with locked_inputs((alias/self.source.name,)):
                pass

    def test_receipt_recovery_under_lock(self):
        before=(self.source.read_bytes(),self.migrated.read_bytes())
        recover_receipt(self.source,self.migrated,self.receipt)
        self.assertEqual(before,(self.source.read_bytes(),self.migrated.read_bytes()))
        self.assertEqual(verify_main([str(self.source),str(self.migrated),str(self.receipt)]),0)

    @unittest.skipUnless(os.name=="posix","POSIX advisory locks only")
    def test_exclusive_lock_blocks_recovery(self):
        import fcntl
        fd=os.open(self.source,os.O_RDONLY)
        try:
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaisesRegex(ValueError,"locked"):
                recover_receipt(self.source,self.migrated,self.receipt)
            self.assertFalse(self.receipt.exists())
        finally:
            os.close(fd)

if __name__=="__main__":
    unittest.main()
