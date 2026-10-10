import unittest
from cn_reits.operating import operating,debt_schedule
from cn_reits.disclosure import distribution_plan
S={'kind':'teaching','description':'原创教学假设'}
class OperatingTests(unittest.TestCase):
    def test_property_driver(self):
        x={'assetModel':'property','date':'2026-12-31','drivers':{'rentableArea':100,'occupancy':.8,'annualRentPerArea':10,'otherRevenue':20},'operatingCosts':[{'id':'cost','amount':100,'source':S}],'cashTaxes':20,'maintenanceCapex':30,'growthCapex':0,'workingCapitalIncrease':10,'source':S}
        self.assertEqual(operating(x)['freeCashFlow'],'660.0')
        x['drivers']['occupancy']=1.1
        with self.assertRaises(ValueError):operating(x)
    def test_debt_act365(self):
        x={'openingPrincipal':100,'source':S,'periods':[{'start':'2025-01-01','end':'2026-01-01','annualRate':.05,'newBorrowingAtStart':0,'principalRepaidAtEnd':20,'cashBeforeDebtService':50,'source':S}]}
        r=debt_schedule(x)['periods'][0];self.assertEqual(r['interestACT365'],'5.00');self.assertEqual(r['closingPrincipal'],'80');self.assertEqual(r['debtServiceCoverage'],'2')
        x['periods'][0]['principalRepaidAtEnd']=101
        with self.assertRaises(ValueError):debt_schedule(x)
    def test_plan_is_not_payment(self):
        x={'code':'508001','asOf':'2025-06-10','periodStart':'2024-01-01','periodEnd':'2024-12-31','availablePeriod':'430707979.93','previouslyDistributed':'213899959.75','remainingAvailable':'216808020.18','plannedTotal':'216800000','plannedPerTenUnits':'4.3362','plannedOnExchangePaymentDate':'2025-06-18','plannedOffExchangePaymentDate':'2025-06-16','source':S}
        r=distribution_plan(x);self.assertIsNone(r['actualPaid']);self.assertEqual(r['plannedPerUnit'],'0.43362');self.assertNotEqual(r['planToRemainingRatio'],r['planToPeriodRatio'])
        x['remainingAvailable']='1'
        with self.assertRaises(ValueError):distribution_plan(x)
