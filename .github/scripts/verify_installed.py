import tempfile,subprocess,sys,os
from pathlib import Path
with tempfile.TemporaryDirectory(prefix='isolated-cn-reits-research-') as folder:
 env=dict(os.environ);env.pop('PYTHONPATH',None);env.update(PYTHONUTF8='1')
 r=subprocess.run([sys.executable,'-I','-m','cn_reits','demo','--out-dir',str(Path(folder)/'demo')],cwd=folder,env=env,capture_output=True,encoding='utf-8',errors='replace')
 if r.returncode:raise SystemExit(r.stderr+r.stdout)
 expected=Path(folder)/'demo'/'report.html'
 assert expected.is_file()
 r=subprocess.run([sys.executable,'-I','-c',"import importlib.util;assert all(importlib.util.find_spec(x) is None for x in ['numpy','pandas','scipy','cnlookthrough','research_workbench','portfolio_engine'])"],cwd=folder,env=env)
 assert r.returncode==0
import cn_reits,importlib.metadata
assert cn_reits.__version__==importlib.metadata.version('cn-reits-research')
print('Installed package completed minimum flow without other author repos or analysis packages')
