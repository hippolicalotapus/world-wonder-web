import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from reviewer_attestation import load_private, main
from publication_manifest import prepare
from independent_review import make_attestation

NOW = "2026-11-12T22:00:00Z"
def fixture():
    return [{"id": "fictional", "title": "Fictional", "collection": "Kindness",
             "summary": "Test fixture", "claim_type": "unverified_report",
             "review_status": "published",
             "sources": [{"title": "Example", "url": "https://example.org",
                          "publisher": "Example", "accessed_on": "2026-11-12",
                          "source_type": "secondary", "rights_status": "link_only"}],
             "internal_review_history": [{"from": "rights_review", "to": "approved",
                 "reviewer": "Editor One", "reason": "Checked", "timestamp": NOW}]}]

class ReviewerAttestationCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        folder = Path(self.tmp.name)
        self.source = folder / "editorial.json"
        self.manifest = folder / "manifest.json"
        self.attestation = folder / "attestation.json"
        self.records = fixture()
        self.source.write_text(json.dumps(self.records))
        self.manifest.write_text(json.dumps(prepare(self.records)))

    def test_prepare_then_validate(self):
        main(["prepare", str(self.source), str(self.manifest), str(self.attestation),
              "--reviewer", "Editor Two", "--timestamp", NOW])
        self.assertTrue(self.attestation.exists())
        main(["validate", str(self.source), str(self.manifest), str(self.attestation)])

    def test_preparation_refuses_overwrite(self):
        main(["prepare", str(self.source), str(self.manifest), str(self.attestation),
              "--reviewer", "Editor Two", "--timestamp", NOW])
        with self.assertRaises(FileExistsError):
            main(["prepare", str(self.source), str(self.manifest), str(self.attestation),
                  "--reviewer", "Editor Two", "--timestamp", NOW])

    def test_same_reviewer_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must differ"):
            main(["prepare", str(self.source), str(self.manifest), str(self.attestation),
                  "--reviewer", "Editor One", "--timestamp", NOW])
        self.assertFalse(self.attestation.exists())

    def test_stale_source_rejected(self):
        self.records[0]["summary"] = "Changed"
        self.source.write_text(json.dumps(self.records))
        with self.assertRaisesRegex(ValueError, "source changed"):
            main(["prepare", str(self.source), str(self.manifest), str(self.attestation),
                  "--reviewer", "Editor Two", "--timestamp", NOW])

    def test_public_catalogue_cannot_be_private_input(self):
        with self.assertRaisesRegex(ValueError, "public catalogue"):
            load_private(self.source.parent / "public-catalogue.json")

if __name__ == "__main__":
    unittest.main()
