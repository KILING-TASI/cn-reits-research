import copy,json,unittest
from pathlib import Path
from cn_reits.public_case import review

class Tests(unittest.TestCase):
    def sample(self):return json.loads((Path(__file__).resolve().parents[1]/'examples/zhangjiang-2025-cash-study.json').read_text('utf-8'))
    def test_real_selected_bridges_and_valuation_gaps(self):
        r=review(self.sample());self.assertEqual(float(r['bridgeDifference']),0);self.assertEqual(float(r['cashBridgeDifference']),0);self.assertFalse(r['paymentPeriodComparable']);self.assertEqual(r['scenarios'][0]['fullAssetValue'],None)
    def test_inconsistent_bridge_is_blocked(self):
        s=self.sample();next(f for f in s['facts'] if f['id']=='availableCash')['value']='1'
        with self.assertRaisesRegex(ValueError,'勾稽'):review(s)
    def test_historical_cutoff_cannot_use_later_report(self):
        s=self.sample();s['asOf']='2025-12-31'
        with self.assertRaisesRegex(ValueError,'截止'):review(s)
    def test_future_cash_not_promoted_to_fact(self):
        s=self.sample();s['scenarios'][0]['basis']='reported'
        with self.assertRaisesRegex(ValueError,'假设'):review(s)
    def test_complete_conditional_case_preserves_unknown_market_price(self):
        s=json.loads((Path(__file__).resolve().parents[1]/'examples/zhangjiang-2025-conditional-study.json').read_text('utf-8'))
        r=review(s);self.assertEqual(r['fullValuationStatus'],'conditional-full-declared-valuation');self.assertIsNone(r['valuation']['scenarioGapRatio']);self.assertEqual(len(r['valuation']['sensitivity']),9)
        for project in r['valuation']['projects']:self.assertEqual(project['cashFlows'][-1]['date'],project['rightsEndDate'])
    def test_changed_rights_end_blocks_conditional_valuation(self):
        s=json.loads((Path(__file__).resolve().parents[1]/'examples/zhangjiang-2025-conditional-study.json').read_text('utf-8'));s['rights'][0]['rightsEndDate']='2099-12-31'
        with self.assertRaisesRegex(ValueError,'权属'):review(s)
    def test_wrong_amount_unit_blocks_arithmetic_bridge(self):
        s=self.sample();s['facts'][0]['unit']='万元'
        with self.assertRaisesRegex(ValueError,'单位'):review(s)
