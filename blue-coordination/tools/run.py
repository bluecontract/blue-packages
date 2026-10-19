"""Run against an installed runtime verified against the current package home."""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'tools'))
from verify_runtime import verify_current_runtime
verify_current_runtime()
command=sys.argv[1] if len(sys.argv)>1 else 'verify'
if command=='test':args=['-m','unittest','discover','-s',str(ROOT/'tests'),'-p','test_*.py','-v']
elif command=='examples':args=[str(ROOT/'tools/examples.py')]
else:args=[str(ROOT/'tools/package.py'),command]
raise SystemExit(subprocess.run([sys.executable,*args,*sys.argv[2:]],cwd=ROOT).returncode)
