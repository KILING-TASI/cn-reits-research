from pathlib import Path
import subprocess,sys,uuid,os
root=Path(__file__).resolve().parent
out=root/'reports'/('teaching-'+uuid.uuid4().hex[:12])
env=dict(os.environ);env.pop('PYTHONPATH',None)
raise SystemExit(subprocess.call([sys.executable,'-S','-m','cn_reits','demo','--out-dir',str(out)],cwd=root,env=env))
