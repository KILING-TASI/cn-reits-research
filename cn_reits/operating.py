# SPDX-License-Identifier: MIT
"""Declared operating drivers and debt schedules; independent of valuation assumptions."""
from decimal import Decimal
from .valuation import num,day,source

def operating(spec):
    required={'assetModel','date','drivers','operatingCosts','cashTaxes','maintenanceCapex','growthCapex','workingCapitalIncrease','source'}
    if not isinstance(spec,dict) or set(spec)!=required:raise ValueError('经营底稿需完整收入驱动、成本、现金税及资本开支')
    day(spec['date']);source(spec['source'],'经营底稿');drivers=spec['drivers']
    if spec['assetModel']=='property':
        if set(drivers)!={'rentableArea','occupancy','annualRentPerArea','otherRevenue'}:raise ValueError('产权收入需面积、出租率、年租金和其他收入')
        occupancy=num(drivers['occupancy'],'出租率',nonnegative=True)
        if occupancy>1:raise ValueError('出租率超过100%')
        revenue=num(drivers['rentableArea'],'可出租面积',positive=True)*occupancy*num(drivers['annualRentPerArea'],'年单位面积租金',nonnegative=True)+num(drivers['otherRevenue'],'其他收入',nonnegative=True)
    elif spec['assetModel']=='concession':
        if set(drivers)!={'billableVolume','averageTariff','otherRevenue'}:raise ValueError('经营权收入需计费业务量、平均收费和其他收入')
        revenue=num(drivers['billableVolume'],'计费量',nonnegative=True)*num(drivers['averageTariff'],'平均收费',nonnegative=True)+num(drivers['otherRevenue'],'其他收入',nonnegative=True)
    else:raise ValueError('仅支持产权/经营权明确收入驱动')
    costs=spec['operatingCosts']
    if not isinstance(costs,list):raise ValueError('经营成本须为逐项列表')
    seen=set();total=Decimal(0)
    for row in costs:
        if set(row)!={'id','amount','source'} or not row['id'] or row['id'] in seen:raise ValueError('成本需唯一身份、金额及依据')
        seen.add(row['id']);source(row['source'],'经营成本');total+=num(row['amount'],'经营成本',nonnegative=True)
    cash=revenue-total-num(spec['cashTaxes'],'现金税',nonnegative=True)
    fcf=cash-num(spec['maintenanceCapex'],'维护资本开支',nonnegative=True)-num(spec['growthCapex'],'增长资本开支',nonnegative=True)-num(spec['workingCapitalIncrease'],'营运资金增量')
    return {'revenue':str(revenue),'operatingCosts':str(total),'operatingCashAfterTaxBeforeCapex':str(cash),'freeCashFlow':str(fcf),
            'valuationCashFlow':{'date':spec['date'],'operatingCashFlowAfterTax':str(cash),'maintenanceCapex':spec['maintenanceCapex'],'growthCapex':spec['growthCapex'],'workingCapitalIncrease':spec['workingCapitalIncrease'],'source':spec['source']},
            'limitation':'声明驱动的情景；税额不由工具猜算，收入不等于实际已收现金，需核对营运资金及成本范围'}

def debt_schedule(spec):
    if not isinstance(spec,dict) or set(spec)!={'openingPrincipal','periods','source'}:raise ValueError('债务计划需期初本金、逐期计划和依据')
    source(spec['source'],'债务计划');balance=num(spec['openingPrincipal'],'期初本金',nonnegative=True);rows=[];previous=None
    if not isinstance(spec['periods'],list) or not spec['periods']:raise ValueError('债务计划不能为空')
    for row in spec['periods']:
        if set(row)!={'start','end','annualRate','newBorrowingAtStart','principalRepaidAtEnd','cashBeforeDebtService','source'}:raise ValueError('债务期间字段不全')
        start,end=day(row['start']),day(row['end'])
        if end<=start or previous is not None and start!=previous:raise ValueError('债务期间须连续，结束晚于开始')
        source(row['source'],'债务期间');opening=balance;new=num(row['newBorrowingAtStart'],'期初借入',nonnegative=True)
        rate=num(row['annualRate'],'年利率',nonnegative=True);repay=num(row['principalRepaidAtEnd'],'期末偿还',nonnegative=True)
        if repay>opening+new:raise ValueError('偿还超过本金')
        interest=(opening+new)*rate*Decimal((end-start).days)/Decimal(365)
        service=interest+repay;cash=num(row['cashBeforeDebtService'],'偿债前现金');balance=opening+new-repay
        rows.append({'start':row['start'],'end':row['end'],'openingPrincipal':str(opening),'interestACT365':str(interest),'principalRepaid':str(repay),'closingPrincipal':str(balance),'cashAfterDebtService':str(cash-service),'debtServiceCoverage':str(cash/service) if service>0 else None})
        previous=end
    return {'periods':rows,'closingPrincipal':str(balance),'limitation':'期初一次借入、期末一次还本、单利ACT/365情景；不自动处理浮息重置/盘中借还/契约测试。利息和本金不可再扣入未杠杆项目DCF，权益桥单独扣债。'}
