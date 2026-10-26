"""Execute the unpublished specification itself in an isolated temporary tree."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / 'spec/bex-resultvalue-preview.md'


def run_specification(specification, destination, tests=()):
    text = Path(specification).read_text()
    modules = re.findall(r'### `(src/[^`]+\.py)`\n\n```python\n(.*?)\n```', text, re.S)
    expected = {'src/blue_bex/' + name for name in
                ('__init__.py', 'compiler.py', 'gas.py', 'runtime.py', 'values.py')}
    expected.add('src/blue_host/__init__.py')
    assert len(modules) == len(expected) and {name for name, _ in modules} == expected
    for name, code in modules:
        data = (code + '\n').encode()
        digest = hashlib.sha256(data).hexdigest()
        assert f'| `{name}` | `{digest}` |' in text, name
        path = destination / name.removeprefix('src/')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    env = dict(os.environ, PYTHONPATH=str(destination), PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([sys.executable, str(ROOT / 'tests/resultvalue_preview_runner.py'),
                    *tests], env=env, cwd=destination, check=True)


def test_unpublished_specification(tmp_path):
    run_specification(CANDIDATE, tmp_path / 'src')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, default=CANDIDATE)
    parser.add_argument('tests', nargs='*')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='bex-preview-spec-') as temporary:
        run_specification(args.spec, Path(temporary) / 'src', args.tests)
