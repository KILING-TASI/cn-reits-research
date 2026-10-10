import unittest,json,hashlib
from pathlib import Path
class FrozenReceiptTests(unittest.TestCase):
 def test_example_receipts_are_exact_bytes(self):
  root=Path(__file__).resolve().parents[1]/'examples'
  for receipt_file in root.glob('*/receipt.json'):
   receipt=json.loads(receipt_file.read_text(encoding='utf-8'))
   for name,expected in receipt['files'].items():self.assertEqual(hashlib.sha256((receipt_file.parent/name).read_bytes()).hexdigest(),expected,(str(receipt_file),name))
 def test_browser_capture_binding(self):
  folder=Path(__file__).resolve().parents[1]/'examples/reits-demo-accepted';record=json.loads((folder/'browser-acceptance.json').read_text(encoding='utf-8'))
  self.assertEqual(hashlib.sha256((folder/'report.html').read_bytes()).hexdigest(),record['reportSha256'])
  for view in record['viewports']:self.assertEqual(hashlib.sha256((folder/view['screenshot']).read_bytes()).hexdigest(),view['sha256'])
