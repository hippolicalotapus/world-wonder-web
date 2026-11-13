import tempfile
import unittest
from pathlib import Path
from tools.receipt_temp_review import plan_receipt_temp_review

class ReviewPlanTests(unittest.TestCase):
 def test_no_files_needs_no_review(self):
  with tempfile.TemporaryDirectory() as root:
   result=plan_receipt_temp_review(root)
   self.assertFalse(result["review_required"])
   self.assertFalse(result["safe_to_auto_delete"])
 def test_private_temp_is_not_deleted(self):
  with tempfile.TemporaryDirectory() as root:
   temp=Path(root)/".wonder-receipt-sample"
   temp.write_text("private")
   result=plan_receipt_temp_review(root)
   self.assertTrue(result["review_required"])
   self.assertEqual(result["operations_performed"],0)
   self.assertEqual(temp.read_text(),"private")
 def test_symlink_is_not_approved_for_cleanup(self):
  with tempfile.TemporaryDirectory() as root:
   outside=Path(root)/"outside"
   outside.write_text("private")
   (Path(root)/".wonder-receipt-link").symlink_to(outside)
   result=plan_receipt_temp_review(root)
   self.assertEqual(result["files"][0]["kind"],"unsafe")
   self.assertFalse(result["safe_to_auto_delete"])

if __name__=="__main__":unittest.main()
