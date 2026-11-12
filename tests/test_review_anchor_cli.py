import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from review_anchor_cli import main
from review_audit_chain import seal_history

def fixture():
    return [{"id":"fixture","review_status":"published","internal_review_history":
             seal_history([{"from":"rights_review","to":"approved","reviewer":"Editor One",
                            "reason":"Reviewed","timestamp":"2026-11-12T22:00:00Z"}])}]

class AnchorCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.edit=root/"editorial"
        self.vault=root/"vault"
        self.edit.mkdir()
        self.vault.mkdir()
        self.source=self.edit/"records.json"
        self.anchor=self.vault/"anchor.json"
        self.records=fixture()
        self.source.write_text(json.dumps(self.records))

    def test_prepare_and_verify(self):
        main(["prepare",str(self.source),str(self.anchor)])
        self.assertTrue(self.anchor.exists())
        before=self.anchor.read_bytes()
        main(["verify",str(self.source),str(self.anchor)])
        self.assertEqual(self.anchor.read_bytes(),before)

    def test_no_overwrite(self):
        main(["prepare",str(self.source),str(self.anchor)])
        with self.assertRaises(FileExistsError):
            main(["prepare",str(self.source),str(self.anchor)])

    def test_reject_same_directory(self):
        with self.assertRaisesRegex(ValueError,"outside"):
            main(["prepare",str(self.source),str(self.edit/"anchor.json")])

    def test_reject_unsealed_published_history(self):
        self.records[0]["internal_review_history"]=[{"from":"rights_review","to":"approved",
            "reviewer":"Editor One","reason":"Reviewed","timestamp":"2026-11-12T22:00:00Z"}]
        self.source.write_text(json.dumps(self.records))
        with self.assertRaisesRegex(ValueError,"Unsealed"):
            main(["prepare",str(self.source),str(self.anchor)])
        self.assertFalse(self.anchor.exists())

    def test_modified_source_fails_verification(self):
        main(["prepare",str(self.source),str(self.anchor)])
        self.records[0]["internal_review_history"][0]["reason"]="Changed"
        self.source.write_text(json.dumps(self.records))
        with self.assertRaisesRegex(ValueError,"integrity mismatch"):
            main(["verify",str(self.source),str(self.anchor)])

    def test_resealed_source_fails_trusted_anchor(self):
        main(["prepare",str(self.source),str(self.anchor)])
        h=self.records[0]["internal_review_history"][0]
        h["reason"]="Changed"
        self.records[0]["internal_review_history"]=seal_history([
            {k:v for k,v in h.items() if k not in ("previous_hash","entry_hash")}])
        self.source.write_text(json.dumps(self.records))
        with self.assertRaisesRegex(ValueError,"Trusted audit anchor mismatch"):
            main(["verify",str(self.source),str(self.anchor)])

    def test_reject_repository_output(self):
        (self.vault/".git").mkdir()
        with self.assertRaisesRegex(ValueError,"Git repository"):
            main(["prepare",str(self.source),str(self.anchor)])

if __name__=="__main__":
    unittest.main()
