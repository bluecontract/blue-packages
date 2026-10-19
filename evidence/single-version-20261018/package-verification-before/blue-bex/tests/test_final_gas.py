import os
from pathlib import Path
import subprocess
import sys
from release import ROOT, runtime_tree


def test_final_gas_reference_and_conformance_vectors(tmp_path):
    source = runtime_tree(tmp_path / 'src')
    env = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([sys.executable, str(ROOT / 'tests/final_gas_runner.py'),
                    str(ROOT / 'conformance/bex.json')], env=env, check=True)
