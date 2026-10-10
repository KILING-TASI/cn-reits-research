# SPDX-License-Identifier: MIT
"""Explicit multi-project, finite-rights REIT valuation. No guessed missing inputs."""
from datetime import date
from decimal import Decimal,InvalidOperation
import math,hashlib,json

SCHEMA='cn-reits-valuation/1.0'
METHOD='dated-project-fcf-equity-bridge/1.0'

def num(x,label,nonnegative=False,positive=False):
    if isinstance(x,bool) or not isinstance(x,(str,int,float)):raise ValueError(label+'须为明确数值')
    try:v=Decimal(str(x))
    except InvalidOperation as e:raise ValueError(label+'无效') from e
    if not v.is_finite() or nonnegative and v<0 or positive and v<=0:raise ValueError(label+'须有限且满足符号范围')
    return v

def day(x):
    if not isinstance(x,str) or len(x)!=10:raise ValueError('日期须为YYYY-MM-DD')
    return date.fromisoformat(x)

def discount(value,rate,days):
    if rate<=-1:raise ValueError('折现率须大于-100%')
    if not math.isfinite(float(rate)):raise ValueError('折现率超出可计算范围')
    try:factor=(1+float(rate))**(days/365.0)
    except OverflowError as exc:raise ValueError('折现系数超出可计算范围') from exc
    if not math.isfinite(factor) or factor<=0:raise ValueError('折现系数不可估')
    return value/Decimal(str(factor))

def source(x,label):
    if not isinstance(x,dict) or not isinstance(x.get('description'),str) or not x['description'].strip():raise ValueError(label+'须声明依据描述')
    if x.get('kind') not in {'reported','assumption','teaching'}:raise ValueError(label+'须区分披露、假设和教学')
    if x['kind']=='reported':
        if not isinstance(x.get('url'),str) or not x['url'].startswith('https://') or not isinstance(x.get('publishedAt'),str):raise ValueError('披露依据需URL和发布日期')
        day(x['publishedAt'])
    return x

def project(p,asof,rate_shift=Decimal(0),cash_shift=Decimal(0)):
    required={'id','assetModel','rightsEndDate','ownership','discountRate','cashFlows','terminal','source'}
    if not isinstance(p,dict) or set(p)!=required:raise ValueError('项目需完整声明身份、资产模型、经营权期限、归属、折现率、现金流、终值和依据')
    source(p['source'],'项目')
    if p['assetModel'] not in {'property','concession'}:raise ValueError('资产模型须为property或concession')
    end=day(p['rightsEndDate']);ownership=num(p['ownership'],'权益归属',positive=True)
    if ownership>1:raise ValueError('权益归属须不超过100%')
    rate=num(p['discountRate'],'项目折现率')+rate_shift
    flows=p['cashFlows']
    if not isinstance(flows,list) or not flows:raise ValueError('项目现金流不能为空，缺年不得填零')
    dates=[day(r['date']) for r in flows]
    if dates!=sorted(set(dates)) or any(not asof<d<=end for d in dates):raise ValueError('现金流须升序唯一，晚于估值日且不超过经营权期限')
    rows=[];pv=Decimal(0)
    for row,d in zip(flows,dates):
        if set(row)!={'date','operatingCashFlowAfterTax','maintenanceCapex','growthCapex','workingCapitalIncrease','source'}:raise ValueError('现金流项缺失或含不支持字段；不得默认缺失费用为零')
        source(row['source'],'现金流')
        operating=num(row['operatingCashFlowAfterTax'],'税后未扣资本开支与营运资金的经营现金')*(1+cash_shift)
        maintain=num(row['maintenanceCapex'],'维护资本开支',nonnegative=True)
        growth=num(row['growthCapex'],'增长资本开支',nonnegative=True)
        working=num(row['workingCapitalIncrease'],'营运资金增量')
        fcf=operating-maintain-growth-working
        present=discount(fcf,rate,(d-asof).days)
        pv+=present;rows.append({'date':row['date'],'freeCashFlow':str(fcf),'presentValue':str(present),'source':row['source']})
    terminal=p['terminal']
    if not isinstance(terminal,dict) or set(terminal)!={'date','netProceeds','method','source'}:raise ValueError('终值需日期、净回收金额、方法和依据，即使为0也须声明')
    td=day(terminal['date']);net=num(terminal['netProceeds'],'终值净回收额',nonnegative=True)
    source(terminal['source'],'终值')
    if not dates[-1]<=td<=end:raise ValueError('终值不得早于末次现金流或晚于经营权期限')
    if terminal['method'] not in {'declared-exit','contract-expiry'}:raise ValueError('不默认永续增长或续期，需明确退出或到期回收')
    if p['assetModel']=='concession' and (td!=end or terminal['method']!='contract-expiry'):raise ValueError('经营权类须逐期覆盖至到期，使用明确到期回收额，不套产权退出')
    if p['assetModel']=='concession' and dates[-1]!=end:raise ValueError('经营权类末期现金流须覆盖明确到期日，不静默截断')
    terminal_pv=discount(net,rate,(td-asof).days);pv+=terminal_pv
    return {'id':p['id'],'assetModel':p['assetModel'],'rightsEndDate':p['rightsEndDate'],'cashFlows':rows,
            'discountRate':str(rate),'terminalPresentValue':str(terminal_pv),'enterpriseValue':str(pv),
            'ownership':str(ownership),'attributableEnterpriseValue':str(pv*ownership),
            'assumptionStatus':'declared-not-independently-verified'}

def evaluate(spec,rate_shift=Decimal(0),cash_shift=Decimal(0)):
    required={'schemaVersion','entity','asOf','currency','fundUnits','marketPrice','marketPriceDate','projects',
              'fundDiscountRate','fundExpenses','excessCash','restrictedCash','debtPrincipal','otherSeniorClaims',
              'nonOperatingAssets','equityBridgeSource','distributionPeriod','distributions','expansion'}
    if not isinstance(spec,dict) or set(spec)!=required:raise ValueError('估值输入缺完整字段或含不支持字段；缺项不猜')
    if spec['schemaVersion']!=SCHEMA or spec['currency']!='CNY':raise ValueError('仅支持首版schema与明确CNY口径')
    asof=day(spec['asOf'])
    if spec['marketPrice'] is None:
        if spec['marketPriceDate'] is not None:raise ValueError('价格未知时不能声明价格日期')
        price=None
    else:
        price_date=day(spec['marketPriceDate'])
        if price_date>asof:raise ValueError('价格日期晚于估值日')
        price=num(spec['marketPrice'],'观察价格',positive=True)
    units=num(spec['fundUnits'],'基金总份额',positive=True)
    if not isinstance(spec['projects'],list) or not spec['projects']:raise ValueError('需要项目现金流')
    ids=[p['id'] for p in spec['projects']]
    if any(not isinstance(i,str) or not i for i in ids) or len(set(ids))!=len(ids):raise ValueError('项目id须唯一且非空')
    projects=[project(p,asof,rate_shift,cash_shift) for p in spec['projects']]
    ev=sum((Decimal(p['attributableEnterpriseValue']) for p in projects),Decimal(0))
    rate=num(spec['fundDiscountRate'],'基金费用折现率')+rate_shift
    expenses=spec['fundExpenses']
    if not isinstance(expenses,list):raise ValueError('基金费用须明确列表；无额外费用也需声明空列表及口径依据')
    dates=[day(r['date']) for r in expenses]
    if dates!=sorted(set(dates)) or any(d<=asof for d in dates):raise ValueError('基金费用日期须为升序唯一未来日期')
    fees=Decimal(0)
    for row,d in zip(expenses,dates):
        if set(row)!={'date','amount','source'}:raise ValueError('基金费用需日期、金额、依据')
        source(row['source'],'基金费用');fees+=discount(num(row['amount'],'基金费用',nonnegative=True),rate,(d-asof).days)
    source(spec['equityBridgeSource'],'基金到权益桥')
    cash=num(spec['excessCash'],'额外可归属现金',nonnegative=True)
    restricted=num(spec['restrictedCash'],'受限现金',nonnegative=True)
    debt=num(spec['debtPrincipal'],'债务本金',nonnegative=True)
    senior=num(spec['otherSeniorClaims'],'其他优先索偿',nonnegative=True)
    nonop=num(spec['nonOperatingAssets'],'非经营资产',nonnegative=True)
    equity=ev-fees+cash+nonop-debt-senior
    distribution=distributions(spec,asof,price)
    result={'schemaVersion':SCHEMA,'methodVersion':METHOD,'entity':spec['entity'],'asOf':spec['asOf'],
            'projects':projects,'enterpriseValue':str(ev),'fundExpensePresentValue':str(fees),
            'equityBridge':{'excessCash':str(cash),'restrictedCashExcluded':str(restricted),'nonOperatingAssets':str(nonop),
                            'debtPrincipal':str(debt),'otherSeniorClaims':str(senior)},
            'equityValue':str(equity),'fundUnits':str(units),'scenarioValuePerUnit':str(equity/units),
            'observedMarketPrice':None if price is None else str(price),'observedMarketPriceDate':spec['marketPriceDate'],
            'scenarioGapRatio':None if price is None else str((equity/units)/price-1),'distribution':distribution,
            'valuationStatus':'conditional-declared-inputs-not-fair-price-certified',
            'unknown':['原文身份、完整经营假设与现金分类未由计算认证','现金流逐期输入不证明已经覆盖全部经营周期',
                       '租金、出租率、收费、续约、融资与退出值均须独立研究','权益桥声明不可含已在项目现金流重复计入的现金或费用',
                       '没有交易执行或估值有效性的保证']}
    return result

def distributions(spec,asof,price):
    period=spec['distributionPeriod']
    if not isinstance(period,dict) or set(period)!={'start','end'}:raise ValueError('分派观察区间需明确起止日')
    start,end=day(period['start']),day(period['end'])
    if start>end or end>asof:raise ValueError('分派区间须为已发生且截至研究日')
    rows=spec['distributions']
    if not isinstance(rows,list):raise ValueError('分派须为明确列表，不从可供分配金额推断实际支付')
    seen=set();total=Decimal(0);accepted=[];excluded=[]
    for row in rows:
        if set(row)!={'id','periodStart','periodEnd','paidDate','totalPaid','unitsAtRecordDate','reportedPerUnit','tolerancePerUnit','source'}:raise ValueError('分派需期间、支付日、金额、登记日份额、每份额及核对精度')
        if not isinstance(row['id'],str) or row['id'] in seen:raise ValueError('分派id重复或无效')
        seen.add(row['id']);source(row['source'],'实际分派')
        ps,pe,pd=day(row['periodStart']),day(row['periodEnd']),day(row['paidDate'])
        if ps>pe or pd<ps:raise ValueError('分派期间或支付日期无效')
        per=num(row['totalPaid'],'实际分派金额',nonnegative=True)/num(row['unitsAtRecordDate'],'登记日份额',positive=True)
        reported=num(row['reportedPerUnit'],'披露每份分派',nonnegative=True)
        tolerance=num(row['tolerancePerUnit'],'披露精度',nonnegative=True)
        if abs(per-reported)>tolerance:raise ValueError('分派总额、份额与每份金额不一致')
        if ps<start or pe>end or pd>asof:excluded.append({'id':row['id'],'reason':'所属期间或支付时点超出本次观察范围'})
        else:total+=reported;accepted.append(row['id'])
    return {'period':period,'acceptedIds':accepted,'excluded':excluded,
            'cashPaidPerUnit':str(total) if accepted else None,
            'periodCashDistributionYield':str(total/price) if accepted and price is not None else None,
            'annualized':False,'coverage':'declared-payments-not-complete-certified'}

def expansion(spec,base_result):
    x=spec['expansion']
    if x is None:return {'status':'not-requested'}
    required={'newProjects','newUnits','issuePrice','issueCosts','newDebt','purchaseConsideration','additionalFundExpenses','source'}
    if not isinstance(x,dict) or set(x)!=required:raise ValueError('扩募须明确项目、份额、发行价、费用、新债和收购对价')
    source(x['source'],'扩募');new_units=num(x['newUnits'],'新增份额',positive=True)
    price=num(x['issuePrice'],'扩募发行价',positive=True);cost=num(x['issueCosts'],'扩募发行费用',nonnegative=True)
    debt=num(x['newDebt'],'新增债务',nonnegative=True);purchase=num(x['purchaseConsideration'],'收购对价',nonnegative=True)
    if not isinstance(x['newProjects'],list) or not x['newProjects']:raise ValueError('扩募需要新增项目')
    all_ids=[p['id'] for p in spec['projects']+x['newProjects']]
    if len(set(all_ids))!=len(all_ids):raise ValueError('扩募项目与现有项目重复')
    projects=[project(p,day(spec['asOf'])) for p in x['newProjects']]
    acquired=sum((Decimal(p['attributableEnterpriseValue']) for p in projects),Decimal(0))
    additional=x['additionalFundExpenses']
    if not isinstance(additional,list):raise ValueError('扩募新增基金层费用须明确列表，无新增也须声明空列表')
    dates=[day(r['date']) for r in additional]
    if dates!=sorted(set(dates)) or any(d<=day(spec['asOf']) for d in dates):raise ValueError('扩募费用须未来升序唯一日期')
    fee_pv=Decimal(0)
    for row,d in zip(additional,dates):
        if set(row)!={'date','amount','source'}:raise ValueError('扩募新增基金费用需日期、金额和依据')
        source(row['source'],'扩募基金费用');fee_pv+=discount(num(row['amount'],'扩募基金费用',nonnegative=True),num(spec['fundDiscountRate'],'基金折现率'),(d-day(spec['asOf'])).days)
    remaining=new_units*price+debt-purchase-cost
    if remaining<0:raise ValueError('扩募资金不足；不能隐含补融资')
    equity=Decimal(base_result['equityValue'])+acquired-fee_pv+remaining-debt
    units=Decimal(base_result['fundUnits'])+new_units
    per=equity/units
    return {'status':'declared-expansion-scenario','newProjectEnterpriseValue':str(acquired),
            'additionalFundExpensePresentValue':str(fee_pv),
            'remainingProceeds':str(remaining),'postUnits':str(units),'postEquityValue':str(equity),
            'postScenarioValuePerUnit':str(per),'perUnitChangeRatio':str(per/Decimal(base_result['scenarioValuePerUnit'])-1) if Decimal(base_result['scenarioValuePerUnit'])>0 else None,
            'limitation':'收购时点、融资条款及每份可供分配金额未被此权益估值比较替代；不是扩募一定增厚'}

def analyze(spec):
    def check_sources(obj):
        if isinstance(obj,dict):
            if obj.get('kind')=='reported' and obj.get('publishedAt') is not None and day(obj['publishedAt'])>day(spec['asOf']):
                raise ValueError('披露依据晚于研究截止日，不能用于本次估值')
            for value in obj.values():check_sources(value)
        elif isinstance(obj,list):
            for value in obj:check_sources(value)
    check_sources(spec)
    result=evaluate(spec);result['expansion']=expansion(spec,result)
    result['sensitivity']=[]
    for shift in [Decimal('-0.01'),Decimal(0),Decimal('0.01')]:
        for cash in [Decimal('-0.1'),Decimal(0),Decimal('0.1')]:
            try:
                v=evaluate(spec,shift,cash)
                result['sensitivity'].append({'discountRateShift':str(shift),'operatingCashShift':str(cash),'scenarioValuePerUnit':v['scenarioValuePerUnit'],'status':'calculated'})
            except ValueError as exc:
                result['sensitivity'].append({'discountRateShift':str(shift),'operatingCashShift':str(cash),'scenarioValuePerUnit':None,'status':'blocked','reason':str(exc)})
    result['inputSha256']=hashlib.sha256(json.dumps(spec,ensure_ascii=False,sort_keys=True,allow_nan=False).encode()).hexdigest()
    return result
