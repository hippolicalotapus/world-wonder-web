import tempfile
import unittest
from pathlib import Path
from tools.receipt_recovery_checklist import receipt_recovery_checklist

class RecoveryChecklistTests(unittest.TestCase):
 def test_empty_directory_has_no_actions(self):
  with tempfile.TemporaryDirectory() as root:
   result=receipt_recovery_checklist(root)
   self.assertEqual(result["checklist"],[])
   self.assertFalse(result["requires_operator"])
 def test_private_receipt_never_changed(self):
  with tempfile.TemporaryDirectory() as root:
   path=Path(root)/".wonder-receipt-test"
   path.write_text("private")
   result=receipt_recovery_checklist(root)
   self.assertTrue(result["requires_operator"])
   self.assertFalse(result["checklist"][0]["automatic_cleanup_allowed"])
   self.assertEqual(result["files_modified"],0)
   self.assertEqual(path.read_text(),"private")

if __name__=="__main__":unittest.main()
