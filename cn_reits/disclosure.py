# SPDX-License-Identifier: MIT
"""Separate cumulative available cash, remaining cash, distribution plans and paid evidence."""
from .valuation import num,day,source

def distribution_plan(spec):
    required={'code','asOf','periodStart','periodEnd','availablePeriod','previouslyDistributed','remainingAvailable','plannedTotal','plannedPerTenUnits','plannedOnExchangePaymentDate','plannedOffExchangePaymentDate','source'}
    if not isinstance(spec,dict) or set(spec)!=required:raise ValueError('分配公告核对需完整期间、累计/已分配/剩余、方案金额和场内外日期')
    if day(spec['periodStart'])>day(spec['periodEnd']) or day(spec['periodEnd'])>day(spec['asOf']):raise ValueError('分配观察期间无效')
    evidence=source(spec['source'],'分配公告')
    if evidence.get('publishedAt') and day(evidence['publishedAt'])>day(spec['asOf']):raise ValueError('公告晚于研究日')
    total=num(spec['availablePeriod'],'期间累计可供分配',nonnegative=True);prior=num(spec['previouslyDistributed'],'此前已分配',nonnegative=True)
    remaining=num(spec['remainingAvailable'],'剩余可供分配',nonnegative=True);planned=num(spec['plannedTotal'],'拟分配总额',nonnegative=True)
    if total-prior!=remaining:raise ValueError('期间累计减此前已分配不等于剩余金额')
    for key in ('plannedOnExchangePaymentDate','plannedOffExchangePaymentDate'):day(spec[key])
    return {'code':spec['code'],'period':[spec['periodStart'],spec['periodEnd']], 'availablePeriod':str(total),'remainingAvailable':str(remaining),'plannedTotal':str(planned),
            'plannedPerUnit':str(num(spec['plannedPerTenUnits'],'每十份方案',nonnegative=True)/10),
            'planToRemainingRatio':str(planned/remaining) if remaining>0 else None,'planToPeriodRatio':str(planned/total) if total>0 else None,
            'arithmeticCheck':'matched','actualPaid':None,'marketYield':None,'fairValue':None,
            'source':evidence,'paymentSchedule':{'onExchange':spec['plannedOnExchangePaymentDate'],'offExchange':spec['plannedOffExchangePaymentDate']},
            'limitations':['公告计划及发放日期不证明账户实际到账','缺登记份额，不从四舍五入的每十份金额倒推份额','缺价格不算分派率，缺未来经营现金流不编造完整估值','方案/剩余可供分配比例不是年度法定分配比例认证']}
