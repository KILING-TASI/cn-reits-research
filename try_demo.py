from pathlib import Path
import argparse, subprocess, sys, uuid, os
root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description='离线原创教学，不覆盖旧结果')
parser.add_argument('--out-dir',type=Path)
parser.add_argument('--no-open',action='store_true',help='保留命令行结果入口；此启动器不自动打开浏览器')
args=parser.parse_args()
out=args.out_dir.resolve() if args.out_dir else root/'reports'/('teaching-'+uuid.uuid4().hex[:12])
env=dict(os.environ);env.pop('PYTHONPATH',None)
raise SystemExit(subprocess.call([sys.executable,'-S','-m','cn_reits','demo','--out-dir',str(out)],cwd=root,env=env))
