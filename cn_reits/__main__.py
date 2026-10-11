import argparse,json,sys,tempfile,shutil,os,hashlib
from decimal import Decimal
from pathlib import Path
from html import escape
from .valuation import analyze
from .cash import available_cash,lifecycle_irr,compare_available
from .operating import operating,debt_schedule
from .disclosure import distribution_plan

def strict(pairs):
    out={}
    for k,v in pairs:
        if k in out:raise ValueError('重复字段：'+k)
        out[k]=v
    return out

def read(path):
    if not path.is_file() or path.is_symlink() or path.stat().st_size>16*1024*1024:raise ValueError('输入不存在、为链接或超过16MiB')
    def bad(x):raise ValueError('非有限JSON数值：'+x)
    return json.loads(path.read_text(encoding='utf-8-sig'),object_pairs_hook=strict,parse_constant=bad)

def render(result):
    blocks=[]
    values=result if 'property' in result else {'本次研究':result}
    labels={'property':'产权项目估值教学','concession':'经营权到期估值教学','expansion':'扩募权益比较教学','available':'可供分配金额教学','lifecycle':'全周期现金流教学'}
    def display(value,digits=2):
        return '未知' if value is None else format(Decimal(str(value)),',.'+str(digits)+'f')
    for name,item in values.items():
        if 'scenarioValuePerUnit' in item:
            rows=[('声明情景每份额价值（元/份）',display(item['scenarioValuePerUnit'],4)),('观察市场价格（元/份）',display(item['observedMarketPrice'],4)),
                  ('项目企业价值合计（元）',display(item['enterpriseValue'])),('基金费用现值（元）',display(item['fundExpensePresentValue']))]
            table='<table><tr><th>项目</th><th>CNY口径</th></tr>'+''.join('<tr><td>'+escape(k)+'</td><td>'+escape(v)+'</td></tr>' for k,v in rows)+'</table>'
            sensitivity='<table><tr><th>折现率变化（百分点）</th><th>经营现金变化（%）</th><th>情景每份额（元）</th></tr>'+''.join('<tr><td>'+display(Decimal(r['discountRateShift'])*100)+'</td><td>'+display(Decimal(r['operatingCashShift'])*100)+'</td><td>'+display(r['scenarioValuePerUnit'],4)+'</td></tr>' for r in item['sensitivity'])+'</table>'
            content=table+'<p>受限现金排除：'+display(item['equityBridge']['restrictedCashExcluded'])+'元。分派观察不自动年化；九组情景是敏感性比较，不是概率区间。企业价值指项目现金流折现值，基金权益价值还需扣费用和债务。</p>'+sensitivity
            expansion=item.get('expansion',{})
            if expansion.get('status')=='declared-expansion-scenario':
                content+='<h3>扩募前后每份额比较</h3><p>扩募前 '+display(item['scenarioValuePerUnit'],4)+'元/份；扩募后 '+display(expansion['postScenarioValuePerUnit'],4)+'元/份；新增基金费用现值 '+display(expansion['additionalFundExpensePresentValue'])+'元。资金余额 '+display(expansion['remainingProceeds'])+'元；新增债务和份额已分开计入。这是声明即时扩募的权益情景，不能代替每份可供分配增厚比较。</p>'
        elif 'calculatedAvailable' in item:
            content='<p>声明调整后可供分配金额 '+display(item['calculatedAvailable'])+'元；每份 '+display(item['availablePerUnit'],4)+'元。它是利润与逐项调整的算术桥，尚不等于账户实际到账。</p>'
        elif 'irr' in item:
            content='<p>条件全周期年收益率 '+('未知' if item['irr'] is None else display(item['irr']*100)+'%')+'。IRR考虑取得价格、未来分派与到期回收的时间；不能用当年分派率代替。</p>'
        elif 'plannedTotal' in item:
            content='<p>方案拟分配 '+display(item['plannedTotal'])+'元；每份 '+display(item['plannedPerUnit'],5)+'元。期间累计可供分配 '+display(item['availablePeriod'])+'元，剩余可供分配 '+display(item['remainingAvailable'])+'元。</p><p>实际到账：未知；市场分派率：未知；公平估值：未知。场内计划 '+escape(item['paymentSchedule']['onExchange'])+'，场外计划 '+escape(item['paymentSchedule']['offExchange'])+'。</p>'
        else:content='<pre>'+escape(json.dumps(item,ensure_ascii=False,indent=2))+'</pre>'
        blocks.append('<section><h2>'+escape(labels.get(name,name))+'</h2>'+content+'<details><summary>完整依据、结果与缺口</summary><pre>'+escape(json.dumps(item,ensure_ascii=False,indent=2))+'</pre></details></section>')
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>REITs经营估值研究</title><style>body{max-width:1000px;margin:32px auto;padding:0 20px;font:17px/1.7 system-ui;color:#203047}table{width:100%;border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #ddd;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere}section{margin:28px 0}</style><h1>REITs经营估值研究</h1><p>先看口径和缺口：结果为声明现金流下的条件测算，不是已经认证的公平价格或实际可成交价格。教学材料不是真实REIT或未来预测。</p>'+''.join(blocks)+'</html>'

def publish(spec,result,out):
    out=out.absolute()
    if out.exists() or out.is_symlink():raise ValueError('输出必须为新目录，不覆盖历史研究')
    out.parent.mkdir(parents=True,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='.reits-',dir=out.parent))
    try:
        for name,data in [('input.json',spec),('result.json',result)]:
            (stage/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
        (stage/'report.html').write_text(render(result),encoding='utf-8')
        receipt={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.iterdir()}
        (stage/'receipt.json').write_text(json.dumps({'files':receipt,'scope':'摘要验证字节一致，不认证来源和估值判断'},ensure_ascii=False,indent=2),encoding='utf-8')
        os.rename(stage,out);return out
    finally:
        if stage.exists():
            if not stage.resolve().is_relative_to(out.parent.resolve()):raise ValueError('临时目录越界，拒绝清理')
            shutil.rmtree(stage)

def main(argv=None):
    incoming=sys.argv[1:] if argv is None else argv
    if incoming and incoming[0]=='public-case':
        from .public_case import main as public_main
        return public_main(incoming[1:])
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description='REITs现金流与经营估值；输入缺失不补零，不执行交易')
    p.add_argument('command',choices=['demo','value','available','lifecycle','compare-available','operating','debt','distribution-plan'])
    p.add_argument('--input',type=Path);p.add_argument('--out-dir',type=Path,required=True)
    args=p.parse_args(argv)
    try:
        if args.out_dir.exists():raise ValueError('输出目录已存在，旧结果保留')
        if args.command=='demo':
            from .teaching import all_cases
            spec=all_cases();result={name:analyze(data) if name in ['property','concession','expansion'] else available_cash(data) if name=='available' else lifecycle_irr(data) for name,data in spec.items()}
        else:
            if args.input is None:raise ValueError('需要--input提供完整声明底稿')
            spec=read(args.input)
            handlers={'value':analyze,'available':available_cash,'lifecycle':lifecycle_irr,'operating':operating,'debt':debt_schedule,'distribution-plan':distribution_plan,'compare-available':lambda x:compare_available(x['before'],x['after'])}
            result=handlers[args.command](spec)
        out=publish(spec,result,args.out_dir);print('研究结果：'+str(out/'report.html'));print('下一步：逐项核对项目范围、现金流假设、费用、债务、份额和原文版本。');return 0
    except (ValueError,OSError,TypeError,KeyError,ArithmeticError) as exc:
        print('未完成：'+str(exc)+'。下一步：补齐明确字段或修正口径，另选新目录。');return 2

if __name__=='__main__':raise SystemExit(main())
