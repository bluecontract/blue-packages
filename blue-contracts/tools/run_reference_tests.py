"""Run all current contracts_event tests after exact package/reference checks."""
from pathlib import Path
import subprocess, sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from verify_runtime import verify_current_runtime
verify_current_runtime()
import blue_packages
root=Path(blue_packages.__file__).resolve().parents[2]
runner=root/'tools/verify_resource_revision.py'
if not runner.is_file():raise RuntimeError('Reference suites require an editable blue-language-python checkout')
raise SystemExit(subprocess.run([sys.executable,str(runner),'--discover','tests/contracts_event','--output','runs/package-contracts_event.json'],cwd=root).returncode)
