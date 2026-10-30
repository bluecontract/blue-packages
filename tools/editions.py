"""Resolve the default Access Events tree or the explicit preserved Demand candidate."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

EDITIONS = ('access-events', 'demand-scoped')


def edition_root(root, edition='access-events'):
    root = Path(root).resolve()
    if edition == 'access-events':
        return root
    if edition != 'demand-scoped':
        raise ValueError('Unknown edition: ' + edition)
    snapshot = root / 'editions/demand-scoped'
    manifest = json.loads((snapshot / 'edition.json').read_text())
    for name, checksum in manifest.get('sharedConfigs', {}).items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != checksum:
            raise ValueError('Shared package interface changed; update the explicit Demand overlay: ' + name)
    sources = {}
    changed = False
    for name, pin in manifest['files'].items():
        path = snapshot / 'sources' / name if pin['overlay'] else root / name
        data = path.read_bytes()
        checksum = hashlib.sha256(data).hexdigest()
        if pin['overlay'] and checksum != pin['sha256']:
            raise ValueError('Demand overlay checksum differs: ' + name)
        changed |= checksum != pin['sha256']
        sources[name] = data
    fingerprint = hashlib.sha256(b''.join(name.encode() + b'\0' + data
        for name, data in sorted(sources.items())) + (snapshot / 'edition.json').read_bytes() + Path(__file__).read_bytes()).hexdigest()
    selected = root / 'build/demand-scoped'
    state_path = selected / '.edition-state.json'
    if state_path.exists() and json.loads(state_path.read_text())['fingerprint'] == fingerprint:
        return selected
    if selected.exists():
        shutil.rmtree(selected)
    selected.mkdir(parents=True)
    for name, data in sources.items():
        path = selected / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    for name, pin in manifest['archives'].items():
        path = root / pin['path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != pin['sha256']:
            raise ValueError('Demand archive checksum differs: ' + name)
        dist = selected / name / 'dist'
        dist.mkdir(parents=True)
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                target = dist / member.filename
                if not target.resolve().is_relative_to(dist.resolve()):
                    raise ValueError('Unsafe Demand archive path')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(member))
        shutil.copyfile(path, dist / 'package.bluepkg')
    for path in snapshot.glob('*.json'):
        if path.name != 'edition.json':
            shutil.copyfile(path, selected / path.name)
    shutil.copytree(root / 'retained', selected / 'retained')
    shutil.copytree(root / 'docs', selected / 'docs')
    if (root / 'verification').exists():
        shutil.copytree(root / 'verification', selected / 'verification')
    state_path.write_text(json.dumps(dict(fingerprint=fingerprint, needsBuild=changed)))
    return selected


def require_built(root):
    path = root / '.edition-state.json'
    if path.exists() and json.loads(path.read_text())['needsBuild']:
        raise ValueError('Shared Demand sources changed; run build_final_gas.py all --edition demand-scoped first')


def mark_built(root):
    path = root / '.edition-state.json'
    if path.exists():
        state = json.loads(path.read_text())
        state['needsBuild'] = False
        path.write_text(json.dumps(state))
