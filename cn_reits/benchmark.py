# SPDX-License-Identifier: MIT
"""Reproducible bounded model timing; not a market data ingestion or SLA benchmark."""
import argparse,json,time,statistics,platform,hashlib
from pathlib import Path
from copy import deepcopy
from .teaching import valuation,project
from .valuation import analyze

def run(repeats=5):
    results=[]
    for size in [1,10,100]:
        spec=valuation();spec['projects']=[project('teaching-'+str(i)) for i in range(size)]
        raw=json.dumps(spec,ensure_ascii=False,sort_keys=True,allow_nan=False).encode();durations=[];hashes=[]
        for _ in range(repeats):
            start=time.perf_counter();result=analyze(deepcopy(spec));durations.append(time.perf_counter()-start)
            hashes.append(hashlib.sha256(json.dumps(result,ensure_ascii=False,sort_keys=True,allow_nan=False).encode()).hexdigest())
        assert len(set(hashes))==1,'Same frozen inputs changed results'
        results.append({'projects':size,'periodsPerProject':2,'sensitivityScenarios':9,'repeats':repeats,'medianSeconds':statistics.median(durations),'maxSeconds':max(durations),'measurementsSeconds':durations,'inputSha256':hashlib.sha256(raw).hexdigest(),'resultSha256':hashes[0]})
    return {'python':platform.python_version(),'platform':platform.platform(),'processor':platform.processor(),'workloads':results,'scope':'原创教学两期现金流，计入deepcopy及9组敏感性；不含联网、解析PDF、渲染或全市场数据','notGuaranteed':['不同硬件/版本速度不同','不是SLA、内存上界或并发生产压力认证']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.exit(2,'输出已存在；性能记录不得覆盖\n')
    result=run();a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
    print('Bounded reproducible timing saved: '+str(a.out))
if __name__=='__main__':main()
