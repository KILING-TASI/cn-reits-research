from copy import deepcopy
from .valuation import SCHEMA

def source():return {'kind':'teaching','description':'原创合成教学假设，不是真实REIT、市场价格或预测'}

def project(id='park',kind='property'):
    return {'id':id,'assetModel':kind,'rightsEndDate':'2027-12-31' if kind=='concession' else '2055-12-31',
            'ownership':'1','discountRate':'0.1','source':source(),
            'cashFlows':[{'date':d,'operatingCashFlowAfterTax':'100','maintenanceCapex':'10','growthCapex':'0',
                          'workingCapitalIncrease':'0','source':source()} for d in ['2026-12-31','2027-12-31']],
            'terminal':{'date':'2027-12-31','netProceeds':'0' if kind=='concession' else '100',
                        'method':'contract-expiry' if kind=='concession' else 'declared-exit','source':source()}}

def valuation(kind='property'):
    return {'schemaVersion':SCHEMA,'entity':'原创教学园区' if kind=='property' else '原创教学经营权项目','asOf':'2025-12-31',
            'currency':'CNY','fundUnits':'100','marketPrice':'2','marketPriceDate':'2025-12-31','projects':[project(kind=kind)],
            'fundDiscountRate':'0.1','fundExpenses':[{'date':'2026-12-31','amount':'5','source':source()}],
            'excessCash':'10','restrictedCash':'50','debtPrincipal':'100','otherSeniorClaims':'0','nonOperatingAssets':'0',
            'equityBridgeSource':source(),'distributionPeriod':{'start':'2025-01-01','end':'2025-12-31'},
            'distributions':[{'id':'paid-1','periodStart':'2025-01-01','periodEnd':'2025-12-31','paidDate':'2025-12-31',
                              'totalPaid':'20','unitsAtRecordDate':'100','reportedPerUnit':'0.2','tolerancePerUnit':'0.0001','source':source()}],
            'expansion':None}

def available():
    return {'periodStart':'2025-01-01','periodEnd':'2025-12-31','netProfit':'50',
            'adjustments':[{'id':'depreciation','amount':'20','reason':'声明非现金折旧加回','source':source()},
                           {'id':'maintenance','amount':'-10','reason':'声明维护支出扣减','source':source()}],
            'units':'100','reportedAvailable':'60','tolerance':'0.01','source':source()}

def lifecycle():
    return {'asOf':'2025-12-31','pricePerUnit':'100','endDate':'2027-12-31',
            'futureCashPerUnit':[{'date':'2026-12-31','amount':'55','source':source()},{'date':'2027-12-31','amount':'60.5','source':source()}],
            'terminalPerUnit':'0','source':source()}

def all_cases():
    extended=valuation();extended['expansion']={'newProjects':[project('new-park')],'newUnits':'100','issuePrice':'2',
                                              'issueCosts':'20','newDebt':'0','purchaseConsideration':'100','additionalFundExpenses':[],'source':source()}
    return {'property':valuation(),'concession':valuation('concession'),'expansion':extended,'available':available(),'lifecycle':lifecycle()}
