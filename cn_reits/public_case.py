# SPDX-License-Identifier: MIT
"""Dated real REIT facts, distributable bridge and bounded future cash scenarios."""
import argparse,hashlib,json,sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from .valuation import num,discount


def review(spec):
    if not isinstance(spec,dict):raise ValueError('REIT研究底稿须为对象')
    if spec.get('inputSchema')!='reits-public-case/1':raise ValueError('需reits-public-case/1')
    cutoff=date.fromisoformat(spec['asOf']);facts=spec['facts'];ids=set();values={}
    if cutoff.isoformat()!=spec['asOf']:raise ValueError('截止日期须YYYY-MM-DD')
    if not isinstance(facts,list) or not 1<=len(facts)<=200 or any(not isinstance(row,dict) for row in facts):raise ValueError('事实须1至200项结构化记录')
    for row in facts:
        if row['id'] in ids:raise ValueError('事实ID重复')
        ids.add(row['id'])
        if date.fromisoformat(row['publishedAt'])>cutoff:raise ValueError('来源晚于截止日')
        if not row['sourceUrl'].startswith('https://') or type(row['page']) is not int or row['page']<1:raise ValueError('需官方来源及物理页码')
        sha=row['documentSha256']
        if not isinstance(sha,str) or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):raise ValueError('来源摘要无效')
        values[row['id']]=num(row['value'],row['id'])
    needed={'netProfit','depreciation','incomeTaxExpense','incomeTaxAdjustment','receivablesAdjustment','reserveAdjustment','payablesAdjustment','projectPurchaseAdjustment','availableCash','paidCash','units','operatingCashFlow','capex','openingCash','closingCash','area','leasedArea','occupancyPct','previousOccupancyPct','previousAvailableCash'}
    if not needed<=values.keys():raise ValueError('完整案例缺必要事实，不能补零')
    unit_map={'units':'份','area':'平方米','leasedArea':'平方米','occupancyPct':'%','previousOccupancyPct':'%'}
    for row in facts:
        if row['id'] in needed and row['unit']!=unit_map.get(row['id'],'元'):raise ValueError('事实金额、数量或比例单位不一致')
        start,end=date.fromisoformat(row['periodStart']),date.fromisoformat(row['periodEnd'])
        if start>end or end>date.fromisoformat(row['publishedAt']):raise ValueError('事实期间倒置或晚于披露日期')
    if values['units']<=0 or values['area']<=0 or not 0<=values['leasedArea']<=values['area']:raise ValueError('份额、面积或实际出租面积无效')
    bridge=sum((values[k] for k in ['netProfit','depreciation','incomeTaxExpense','incomeTaxAdjustment','receivablesAdjustment','reserveAdjustment','payablesAdjustment','projectPurchaseAdjustment']),Decimal(0))
    gap=bridge-values['availableCash']
    if abs(gap)>Decimal('.01'):raise ValueError('可供分配金额未勾稽；差额不能自动配平')
    cash_gap=values['openingCash']+values['operatingCashFlow']-values['capex']-values['paidCash']-values['closingCash']
    if abs(cash_gap)>Decimal('.01'):raise ValueError('选定年度现金桥未勾稽，需补齐其他现金流')
    occupancy=values['leasedArea']/values['area']*100
    if abs(occupancy-values['occupancyPct'])>Decimal('.01'):raise ValueError('出租面积与出租率不符')
    scenarios=[]
    for scenario in spec['scenarios']:
        if scenario.get('basis')!='assumption' or not isinstance(scenario.get('note'),str) or not scenario['note'].strip():raise ValueError('未来现金流须明确假设及依据')
        rate=num(scenario['discountRate'],'折现率');factor=num(scenario['cashFactor'],'现金情景比例',nonnegative=True)
        if rate<=-1:raise ValueError('折现率须大于-100%')
        dates=scenario['paymentDates'];days=[date.fromisoformat(d) for d in dates]
        if not 1<=len(days)<=30 or days!=sorted(set(days)) or any(d<=cutoff for d in days):raise ValueError('需1至30个明确未来支付日')
        payout=num(scenario['payoutRatio'],'假设分配比例',nonnegative=True)
        if payout>1:raise ValueError('分配比例超过100%')
        cash=values['availableCash']*factor*payout;pv=sum((discount(cash,rate,(d-cutoff).days) for d in days),Decimal(0))
        scenarios.append({'name':scenario['name'],'basis':'assumption','note':scenario['note'],'paymentDates':dates,'annualCash':str(cash),'presentValueOfSelectedPayments':str(pv),'perUnitSelectedPaymentsPresentValue':str(pv/values['units']),'discountRate':str(rate),'terminalValue':None,'fullAssetValue':None})
    unknown=spec['unknown']
    if not isinstance(unknown,list) or not unknown or any(not isinstance(x,str) or not x.strip() for x in unknown):raise ValueError('需明确完整估值未解决项')
    valuation=None
    if spec.get('valuationInput') is not None:
        from .valuation import analyze
        declared=spec['valuationInput']
        if declared['asOf']!=spec['asOf'] or num(declared['fundUnits'],'估值份额')!=values['units']:raise ValueError('估值截止或份额与案例不一致')
        rights={r['projectId']:r for r in spec['rights']}
        if set(rights)!={p['id'] for p in declared['projects']}:raise ValueError('每个估值项目需权属期限来源')
        for project in declared['projects']:
            right=rights[project['id']]
            if right['rightsEndDate']!=project['rightsEndDate'] or date.fromisoformat(right['publishedAt'])>cutoff or not right['sourceUrl'].startswith('https://') or type(right['page']) is not int or right['page']<1:raise ValueError('权属期限来源与估值不符')
            sha=right['documentSha256']
            if not isinstance(sha,str) or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):raise ValueError('权属来源摘要无效')
        valuation=analyze(declared)
    result={'methodVersion':'real-reit-cash-case/1','entity':spec['entity'],'asOf':spec['asOf'],'conclusion':'年度可供分配金额与所选现金流可以复核；支付年度与收益所属期存在差异。未来现金仅作明确情景，当前资料不足以认证完整资产估值。','bridgeAvailableCash':str(bridge),'bridgeDifference':str(gap),'cashBridgeDifference':str(cash_gap),'occupancyPctCalculated':str(occupancy),'occupancyChangePercentagePoints':str(values['occupancyPct']-values['previousOccupancyPct']),'availableCashChangeRatio':str(values['availableCash']/values['previousAvailableCash']-1),'annualAvailablePerUnit':str(values['availableCash']/values['units']),'paidMinusCurrentYearAvailable':str(values['paidCash']-values['availableCash']),'paymentPeriodComparable':False,'paymentInterpretation':'年度实际支付包含上一年度收益分派，不能直接除本年可供分配金额判断超额分派。','scenarios':scenarios,'fullValuationStatus':'conditional-full-declared-valuation' if valuation else 'blocked-missing-rights-terminal-and-complete-assumptions','valuation':valuation,'facts':facts,'humanRows':[['出租率变化（百分点）',str(values['occupancyPct']-values['previousOccupancyPct'])],['可供分配金额',str(bridge)],['当年实际支付',str(values['paidCash'])],['分配期间可比性','包含上一年度收益分派，不能直接相比'],['完整估值','已生成明确底稿下的条件估值；不认证合理价格' if valuation else '资料未齐，保持未知']],'limitations':unknown+['未来各年沿用基准现金的情景比例是假设，不是管理人预测','所选未来分派现值不含终值，不能冒充基金公允价值或完整DCF','事实来源和页码可复查；程序不认证原件真实性或投资价值']}
    if valuation:result['conclusion']=f"本例合并净利润为{values['netProfit']:,.2f}元，折旧摊销加回{values['depreciation']:,.2f}元，再结合所列调整形成正的可供分配金额；净利润为负不能直接等同现金不足。出租率较上年末变化{values['occupancyPct']-values['previousOccupancyPct']:.2f}个百分点。两项目按历史披露期限与明确未来假设计算条件估值，分派和当前交易价格分别处理。"
    return result


def main(argv=None):
    from html import escape
    p=argparse.ArgumentParser(description='真实REIT年度经营、现金和分派研究；完整估值缺项明确阻断')
    p.add_argument('--input',type=Path,required=True);p.add_argument('--out-dir',type=Path,required=True);a=p.parse_args(argv)
    try:
        if a.out_dir.exists():raise ValueError('输出已存在，旧报告不覆盖')
        if not a.input.is_file() or a.input.is_symlink() or a.input.stat().st_size>16*1024*1024:raise ValueError('需不超过16MiB普通JSON')
        from .__main__ import read
        spec=read(a.input);r=review(spec);a.out_dir.mkdir(parents=True)
        for name,obj in [('input.json',spec),('result.json',r)]:
            (a.out_dir/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),'utf-8')
        rows='<tr><th>核对项</th><th>本次结果</th></tr>'+''.join('<tr><td>'+escape(str(k))+'</td><td>'+escape(format(Decimal(v),',.2f') if k in {'可供分配金额','当年实际支付'} else str(v))+'</td></tr>' for k,v in r['humanRows'])
        scenarios='<tr><th>情景</th><th>所选支付现值（元/份）</th><th>假设</th></tr>'+''.join('<tr><td>'+escape(s['name'])+'</td><td>'+format(Decimal(s['perUnitSelectedPaymentsPresentValue']),'.4f')+'</td><td>'+escape(s['note'])+'</td></tr>' for s in r['scenarios'])
        names={'netProfit':'合并净利润','depreciation':'折旧摊销','incomeTaxExpense':'所得税费用','incomeTaxAdjustment':'所得税调整','receivablesAdjustment':'应收项目调整','reserveAdjustment':'预留支出调整','payablesAdjustment':'应付项目调整','projectPurchaseAdjustment':'购买项目支出调整','availableCash':'本年可供分配金额','previousAvailableCash':'上年可供分配金额','paidCash':'本年实际分配金额','units':'基金份额','operatingCashFlow':'经营现金流净额','capex':'购建长期资产支付现金','openingCash':'期初现金及等价物','closingCash':'期末现金及等价物','area':'可供出租面积','leasedArea':'实际出租面积','occupancyPct':'本年末出租率','previousOccupancyPct':'上年末出租率'}
        facts='<tr><th>事实</th><th>原单位金额或数量</th><th>原页</th></tr>'+''.join('<tr><td>'+escape(names.get(f['id'],f['id']))+'</td><td>'+escape(format(Decimal(f['value']),',.2f'))+' '+escape(f['unit'])+'</td><td><a href="'+escape(f['sourceUrl'],quote=True)+'">第'+str(f['page'])+'页</a></td></tr>' for f in spec['facts'])
        html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>真实REIT研究过程</title><style>body{max-width:1050px;margin:32px auto;padding:0 18px;font:17px/1.7 system-ui}table{width:100%;border-collapse:collapse}td{padding:9px;border-bottom:1px solid #ddd;overflow-wrap:anywhere}.table{overflow:auto}</style><h1>'+escape(spec['question'])+'</h1><p>'+escape(r['conclusion'])+'</p><div class="table"><table>'+rows+'</table></div><h2>明确假设下的未来现金情景</h2><p>只折现所列支付，不含终值；下表不能当作每份基金合理价格。</p><div class="table"><table>'+scenarios+'</table></div><h2>事实底稿</h2><details><summary>展开事实、单位和原页</summary><div class="table"><table>'+facts+'</table></div></details><h2>哪些资料会改变判断</h2><ul>'+''.join('<li>'+escape(x)+'</li>' for x in r['limitations'])+'</ul><p>查看 input.json、result.json 和 receipt.json 复现本次参数与结果。原文不随程序分发。</p></html>'
        if r['valuation']:
            value=r['valuation'];grid='<tr><th>折现率变化（百分点）</th><th>经营现金变化</th><th>条件价值（元/份）</th></tr>'+''.join('<tr><td>'+format(Decimal(row['discountRateShift'])*100,'.0f')+'</td><td>'+format(Decimal(row['operatingCashShift']),'.0%')+'</td><td>'+('未知' if row['scenarioValuePerUnit'] is None else format(Decimal(row['scenarioValuePerUnit']),'.4f'))+'</td></tr>' for row in value['sensitivity'])
            section='<h2>两项目完整底稿下的条件估值</h2><p>基础情景每份 '+format(Decimal(value['scenarioValuePerUnit']),'.4f')+' 元；项目现值合计 '+format(Decimal(value['enterpriseValue']),',.2f')+' 元；基金费用现值 '+format(Decimal(value['fundExpensePresentValue']),',.2f')+' 元。当前市场价格未知，不给出价差或交易结论。</p><p>属于敏感性情景，不是概率区间。</p><div class="table"><table>'+grid+'</table></div><p>项目现金流按2026年剩余期间至各自已披露土地到期日逐年列出；不自动续期。全部经营转化率、未来费用、零退出回收及权益桥假设见 input.json。</p>'
            html=html.replace('<h2>事实底稿</h2>',section+'<h2>事实底稿</h2>')
        (a.out_dir/'report.html').write_text(html,'utf-8');(a.out_dir/'receipt.json').write_text(json.dumps({'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.out_dir.iterdir()},'methodVersion':r['methodVersion']},indent=2),'utf-8')
        print('研究过程已保存：'+str(a.out_dir/'report.html'));return 0
    except (ValueError,KeyError,TypeError,OSError) as exc:print('未完成：'+str(exc),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
