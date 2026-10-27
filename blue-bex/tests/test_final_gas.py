import os
import re
from pathlib import Path
import subprocess
import sys
from release import ROOT, runtime_tree


def test_final_gas_reference_and_conformance_vectors(tmp_path):
    source = runtime_tree(tmp_path / 'src')
    # Historical expectations execute the unchanged frozen final-gas algorithms.
    frozen = (ROOT / 'spec/bex-final-gas.md').read_text()
    for name, code in re.findall(r'### `(src/[^`]+\.py)`\n\n```python\n(.*?)\n```', frozen, re.S):
        (source / name.removeprefix('src/')).write_text(code + '\n')
    env = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([sys.executable, str(ROOT / 'tests/final_gas_runner.py'),
                    str(ROOT / 'conformance/bex.json')], env=env, check=True)


def test_selected_preview_reference_and_conformance_vectors(tmp_path):
    source = runtime_tree(tmp_path / 'src')
    env = dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([sys.executable, str(ROOT / 'tests/final_gas_runner.py'),
                    str(ROOT / 'conformance/resultvalue-preview.json')], env=env, check=True)
