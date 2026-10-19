from pathlib import Path
import sys,os,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from release import checked_package,runtime_tree
checked_package()
with tempfile.TemporaryDirectory(prefix='blue-contracts-runtime-') as d:
    src=runtime_tree(Path(d)/'src')
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(src))
    raise SystemExit(subprocess.run([sys.executable,str(ROOT/'examples/consumer.py')],env=env,cwd=d).returncode)
