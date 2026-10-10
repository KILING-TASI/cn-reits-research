import unittest,copy,tempfile
from decimal import Decimal
from pathlib import Path
from cn_reits.teaching import valuation,available,lifecycle,all_cases,source
from cn_reits.valuation import analyze
from cn_reits.cash import available_cash,lifecycle_irr,compare_available
from cn_reits.__main__ import publish

class ReitsTests(unittest.TestCase):
    def test_hand_calculated_dcf_and_bridge(self):
        result=analyze(valuation());expected=90/1.1+190/1.1**2-5/1.1+10-100
        self.assertAlmostEqual(float(result['equityValue']),expected,places=9)
        self.assertAlmostEqual(float(result['scenarioValuePerUnit']),expected/100,places=9)
    def test_restricted_cash_does_not_inflate_value(self):
        a=valuation();b=copy.deepcopy(a);b['restrictedCash']='5000000'
        self.assertEqual(analyze(a)['equityValue'],analyze(b)['equityValue'])
    def test_concession_cannot_use_property_exit(self):
        a=valuation('concession');a['projects'][0]['terminal']['method']='declared-exit'
        with self.assertRaises(ValueError):analyze(a)
    def test_concession_not_silently_shortened(self):
        a=valuation('concession');a['projects'][0]['cashFlows'].pop()
        with self.assertRaises(ValueError):analyze(a)
    def test_cashflow_after_rights_rejected(self):
        a=valuation();a['projects'][0]['rightsEndDate']='2026-12-31'
        with self.assertRaises(ValueError):analyze(a)
    def test_missing_capex_not_defaulted_zero(self):
        a=valuation();del a['projects'][0]['cashFlows'][0]['maintenanceCapex']
        with self.assertRaises(ValueError):analyze(a)
    def test_duplicate_project_rejected(self):
        a=valuation();a['projects'].append(copy.deepcopy(a['projects'][0]))
        with self.assertRaises(ValueError):analyze(a)
    def test_ownership_applied(self):
        a=valuation();first=analyze(a);a['projects'][0]['ownership']='0.5'
        self.assertAlmostEqual(float(analyze(a)['enterpriseValue']),float(first['enterpriseValue'])/2,places=9)
    def test_rate_sensitivity_has_expected_direction(self):
        r=analyze(valuation());v={x['discountRateShift']:float(x['scenarioValuePerUnit']) for x in r['sensitivity'] if x['operatingCashShift']=='0'}
        self.assertGreater(v['-0.01'],v['0']);self.assertGreater(v['0'],v['0.01'])
    def test_actual_dividend_not_annualized(self):
        d=analyze(valuation())['distribution'];self.assertEqual(d['periodCashDistributionYield'],'0.1');self.assertFalse(d['annualized'])
    def test_declared_dividend_inconsistency_rejected(self):
        a=valuation();a['distributions'][0]['totalPaid']='30'
        with self.assertRaises(ValueError):analyze(a)
    def test_future_payment_excluded(self):
        a=valuation();a['distributions'][0]['paidDate']='2026-01-01'
        self.assertIsNone(analyze(a)['distribution']['cashPaidPerUnit'])
    def test_price_unknown_keeps_dcf_but_no_yield(self):
        a=valuation();a['marketPrice']=None;a['marketPriceDate']=None;r=analyze(a)
        self.assertIsNotNone(r['scenarioValuePerUnit']);self.assertIsNone(r['scenarioGapRatio']);self.assertIsNone(r['distribution']['periodCashDistributionYield'])
    def test_new_fund_fees_reduce_expansion_value(self):
        a=all_cases()['expansion'];base=analyze(a)['expansion']['postEquityValue']
        a['expansion']['additionalFundExpenses']=[{'date':'2026-12-31','amount':'11','source':source()}]
        r=analyze(a)['expansion'];self.assertAlmostEqual(float(base)-float(r['postEquityValue']),10)
    def test_expansion_has_no_implicit_financing(self):
        a=all_cases()['expansion'];a['expansion']['purchaseConsideration']='1000'
        with self.assertRaises(ValueError):analyze(a)
    def test_expansion_equity_bridge_handcheck(self):
        a=all_cases()['expansion'];r=analyze(a);x=r['expansion']
        expected=Decimal(r['equityValue'])+Decimal(r['enterpriseValue'])+Decimal(80)
        self.assertEqual(Decimal(x['postEquityValue']),expected);self.assertEqual(x['postUnits'],'200')
    def test_future_report_cannot_be_used(self):
        a=valuation();a['projects'][0]['source']={'kind':'reported','description':'later report','url':'https://example.org','publishedAt':'2026-01-01'}
        with self.assertRaises(ValueError):analyze(a)
    def test_available_cash_is_not_net_profit(self):
        r=available_cash(available());self.assertEqual(r['calculatedAvailable'],'60');self.assertEqual(r['availablePerUnit'],'0.6')
    def test_available_comparison_requires_same_period(self):
        a,b=available(),available();b['periodEnd']='2025-06-30'
        with self.assertRaises(ValueError):compare_available(a,b)
    def test_finite_lifecycle_unique_irr(self):
        r=lifecycle_irr(lifecycle());self.assertAlmostEqual(r['irr'],0.1,places=9)
    def test_nonconventional_irr_not_arbitrarily_chosen(self):
        a=lifecycle();a['futureCashPerUnit'][1]['amount']='-60'
        self.assertIsNone(lifecycle_irr(a)['irr'])
    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/'r';a=valuation();publish(a,analyze(a),path);old=(path/'result.json').read_bytes()
            with self.assertRaises(ValueError):publish(a,analyze(a),path)
            self.assertEqual((path/'result.json').read_bytes(),old)

if __name__=='__main__':unittest.main()
