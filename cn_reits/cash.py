# SPDX-License-Identifier: MIT
"""Distributable cash reconciliation and conventional finite-life per-unit XIRR."""
from decimal import Decimal
import math
from .valuation import num,day,source

def available_cash(spec):
    fields={'periodStart','periodEnd','netProfit','adjustments','units','reportedAvailable','tolerance','source'}
    if not isinstance(spec,dict) or set(spec)!=fields:raise ValueError('可供分配金额需期间、利润、逐项调整、份额、披露值和核对精度')
    if day(spec['periodStart'])>day(spec['periodEnd']):raise ValueError('可供分配观察期间倒置')
    source(spec['source'],'可供分配底稿')
    total=num(spec['netProfit'],'利润起点');units=num(spec['units'],'同口径份额',positive=True)
    adjustments=spec['adjustments']
    if not isinstance(adjustments,list):raise ValueError('调整项须为明确列表；不自动把利润当现金')
    seen=set()
    for row in adjustments:
        if set(row)!={'id','amount','reason','source'} or not isinstance(row['id'],str) or row['id'] in seen or not row['reason']:raise ValueError('调整项须唯一id、带符号金额、原因和依据')
        seen.add(row['id']);source(row['source'],'可供分配调整');total+=num(row['amount'],'调整金额')
    reported=None if spec['reportedAvailable'] is None else num(spec['reportedAvailable'],'披露可供分配金额')
    tolerance=num(spec['tolerance'],'核对精度',nonnegative=True)
    delta=None if reported is None else total-reported
    return {'periodStart':spec['periodStart'],'periodEnd':spec['periodEnd'],'calculatedAvailable':str(total),
            'availablePerUnit':str(total/units),'units':str(units),'reportedAvailable':None if reported is None else str(reported),
            'difference':None if delta is None else str(delta),
            'reconciliation':'not-comparable' if delta is None else 'within-declared-tolerance' if abs(delta)<=tolerance else 'difference',
            'classificationVerified':False,'limitation':'逐项声明的算术桥，不认证全部调整合法性或实际已支付，不据此自动判定分配比例合规'}

def compare_available(before,after):
    a,b=available_cash(before),available_cash(after)
    if (a['periodStart'],a['periodEnd'])!=(b['periodStart'],b['periodEnd']):raise ValueError('扩募可供分配比较须同期间，不把全年与部分年度并排')
    first=Decimal(a['availablePerUnit']);second=Decimal(b['availablePerUnit'])
    return {'before':a,'after':b,'perUnitDifference':str(second-first),'perUnitChangeRatio':None if first<=0 else str(second/first-1),
            'limitation':'只能比较明确的同口径金额与份额，不保证未来实际增厚'}

def lifecycle_irr(spec):
    if not isinstance(spec,dict) or set(spec)!={'asOf','pricePerUnit','endDate','futureCashPerUnit','terminalPerUnit','source'}:raise ValueError('全周期IRR需价格、截止/到期日期、每份未来现金及终值')
    asof,end=day(spec['asOf']),day(spec['endDate'])
    if end<=asof:raise ValueError('生命周期到期日须晚于研究日')
    price=num(spec['pricePerUnit'],'观察价格',positive=True);terminal=num(spec['terminalPerUnit'],'到期回收额',nonnegative=True)
    if not all(math.isfinite(float(v)) for v in (price,terminal)):raise ValueError('金额超出IRR支持范围')
    source(spec['source'],'生命周期情景')
    rows=spec['futureCashPerUnit'];dates=[day(row['date']) for row in rows]
    if not rows or dates!=sorted(set(dates)) or any(not asof<d<=end for d in dates):raise ValueError('生命周期现金需升序唯一且在期限内')
    flows=[]
    for row,d in zip(rows,dates):
        if set(row)!={'date','amount','source'}:raise ValueError('生命周期现金需金额、日期和依据')
        source(row['source'],'生命周期现金');value=num(row['amount'],'每份未来现金')
        if not math.isfinite(float(value)):raise ValueError('金额超出IRR支持范围')
        if value<0:return {'status':'not-estimable','irr':None,'reason':'非传统正负现金流可能多解，本入口不挑选某个IRR根'}
        flows.append((float(value),(d-asof).days/365.0))
    flows.append((float(terminal),(end-asof).days/365.0))
    if not any(value>0 for value,_ in flows):return {'status':'not-estimable','irr':None,'reason':'无正向回款，不能用0表示收益率'}
    def npv(rate):
        log=math.log1p(rate);total=-float(price)
        for value,years in flows:
            try:total+=value*math.exp(-log*years)
            except OverflowError:return math.inf
        return total
    left,right=-0.999999,1.0
    while npv(right)>0 and right<1024:right=right*2+1
    if npv(left)<=0 or npv(right)>=0:return {'status':'not-estimable','irr':None,'reason':'声明现金流无法在支持区间内找到唯一传统IRR'}
    for _ in range(160):
        middle=(left+right)/2
        if npv(middle)>0:left=middle
        else:right=middle
    rate=(left+right)/2
    return {'status':'calculated-conditional','irr':rate,'yearBasis':'ACT/365','npvResidualPerUnit':npv(rate),
            'limitation':'未来分派与到期回收为明确假设；分派率不是全周期收益率，没有执行或兑现保证'}
