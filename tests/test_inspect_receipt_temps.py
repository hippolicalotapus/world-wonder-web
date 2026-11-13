import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from inspect_receipt_temps import inspect_receipt_temps

class ReceiptTempInspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory=Path(self.temp.name)/"private"
        self.directory.mkdir()

    def test_empty_directory(self):
        self.assertEqual(inspect_receipt_temps(self.directory),[])

    def test_detects_leftover_without_reading_or_removing(self):
        temp=self.directory/".wonder-receipt-example"
        temp.write_text("private editorial information")
        original=temp.read_bytes()
        self.assertEqual(inspect_receipt_temps(self.directory),
                         [{"name":temp.name,"kind":"regular","bytes":len(original)}])
        self.assertEqual(temp.read_bytes(),original)

    def test_ignores_unrelated_files(self):
        (self.directory/"other.json").write_text("{}")
        self.assertEqual(inspect_receipt_temps(self.directory),[])

    def test_marks_symlink_unsafe(self):
        outside=Path(self.temp.name)/"outside"
        outside.write_text("secret")
        (self.directory/".wonder-receipt-link").symlink_to(outside)
        self.assertEqual(inspect_receipt_temps(self.directory)[0]["kind"],"unsafe")

    def test_rejects_symlink_directory(self):
        alias=Path(self.temp.name)/"alias"
        alias.symlink_to(self.directory,target_is_directory=True)
        with self.assertRaises((OSError,ValueError)):
            inspect_receipt_temps(alias)

if __name__=="__main__":
    unittest.main()
