from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'tools'))
from verify_runtime import verify_current_runtime
verify_current_runtime()
import subprocess
raise SystemExit(subprocess.run([sys.executable,str(ROOT/'examples/consumer.py')]).returncode)
