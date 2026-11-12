import sys
import tempfile
import unittest
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from publication_manifest import prepare
from export_public_catalogue import guarded_export
from editorial_backup import write_new

def item(state="published"):
    return {"id": "fictional-test", "title": "Fictional fixture",
            "collection": "Kindness", "summary": "Not a real story",
            "claim_type": "unverified_report", "review_status": state,
            "sources": [{"title": "Example", "publisher": "Example",
                         "url": "https://example.org/story",
                         "accessed_on": "2026-11-12",
                         "source_type": "secondary", "rights_status": "link_only"}]}

class PublicationManifestTests(unittest.TestCase):
    def test_manifest_matches_published_records(self):
        records = [item()]
        manifest = prepare(records)
        self.assertEqual(manifest["publish_ids"], ["fictional-test"])
        self.assertEqual(len(guarded_export(records, manifest)), 1)

    def test_drafts_are_not_included(self):
        records = [item("draft")]
        manifest = prepare(records)
        self.assertEqual(manifest["publish_ids"], [])
        self.assertEqual(guarded_export(records, manifest), [])

    def test_source_change_invalidates_prepared_manifest(self):
        records = [item()]
        manifest = prepare(records)
        records[0]["summary"] = "Changed after review"
        with self.assertRaisesRegex(ValueError, "source changed"):
            guarded_export(records, manifest)

    def test_pending_rights_block_manifest_preparation(self):
        records = [item()]
        records[0]["sources"][0]["rights_status"] = "permission_pending"
        with self.assertRaisesRegex(ValueError, "pending rights"):
            prepare(records)

    def test_private_fields_block_published_manifest(self):
        records = [item()]
        records[0]["email"] = "private@example.org"
        with self.assertRaisesRegex(ValueError, "private field"):
            prepare(records)

    def test_create_only_manifest_storage(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "private-manifest.json"
            manifest = prepare([item()])
            write_new(path, manifest)
            self.assertEqual(json.loads(path.read_text()), manifest)
            with self.assertRaises(FileExistsError):
                write_new(path, manifest)

if __name__ == "__main__":
    unittest.main()
