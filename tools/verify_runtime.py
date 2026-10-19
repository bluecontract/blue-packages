"""Require the installed Python runtime to match this package home's exact appendices."""
import hashlib
import importlib
import json
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
def verify_current_runtime():
    from blue_packages import PackageStore
    from blue_packages.runtime import publication
    store = PackageStore(ROOT)
    for name in ('blue-language', 'blue-bex', 'blue-contracts', 'blue-dispatch', 'blue-coordination', 'blue-mandates'):
        package = store.package(name)
        if publication(name).archive != package.archive:
            raise ValueError('Installed runtime uses different package bytes: ' + name)
    for name in ('blue-bex','blue-contracts'):
        root = ROOT/name; expected = json.loads((root/'docs/sources.json').read_text())['modules']
        blocks = dict(re.findall(r'### `(src/[a-z_/]+\.py)`\n\n```python\n(.*?)```', (root/'SPECIFICATION.md').read_text(), re.S))
        if set(expected) != set(blocks): raise ValueError('Incomplete executable appendix: ' + name)
        for path, digest in expected.items():
            body = blocks[path].encode()
            if hashlib.sha256(body).hexdigest() != digest.removeprefix('sha256:'):
                raise ValueError('Appendix source hash differs: ' + path)
            module = path.removeprefix('src/').removesuffix('.py').replace('/', '.')
            if module.endswith('.__init__'): module = module[:-9]
            if Path(importlib.import_module(module).__file__).read_bytes() != body:
                raise ValueError('Installed runtime source differs: ' + path)
    return True
if __name__ == '__main__':
    verify_current_runtime()
    print('PASS: installed runtime equals the canonical executable appendices and package bytes')
