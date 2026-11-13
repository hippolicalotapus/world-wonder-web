import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from inspect_receipt_temps import inspect_receipt_temps

class InterruptedReceiptSafetyTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.addCleanup(self.tmp.cleanup)
  self.folder=Path(self.tmp.name)/"private"
  self.folder.mkdir()
 def test_hardlinked_temporary_file_is_unsafe(self):
  outside=Path(self.tmp.name)/"other"
  outside.write_text("private")
  (self.folder/".wonder-receipt-linked").hardlink_to(outside)
  self.assertEqual(inspect_receipt_temps(self.folder)[0]["kind"],"unsafe")
 def test_regular_temporary_file_remains_read_only(self):
  entry=self.folder/".wonder-receipt-ordinary"
  entry.write_text("confidential")
  self.assertEqual(inspect_receipt_temps(self.folder)[0]["kind"],"regular")
  self.assertEqual(entry.read_text(),"confidential")
 def test_replaced_directory_is_not_treated_as_original(self):
  original=self.folder
  moved=Path(self.tmp.name)/"moved"
  original.rename(moved)
  original.mkdir()
  self.assertEqual(inspect_receipt_temps(original),[])
  self.assertTrue(moved.is_dir())

if __name__=="__main__":unittest.main()
