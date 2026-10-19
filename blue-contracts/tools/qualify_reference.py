from pathlib import Path
import subprocess, sys
raise SystemExit(subprocess.run([sys.executable,str(Path(__file__).with_name('run_reference_tests.py'))]).returncode)
