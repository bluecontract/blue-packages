#!/usr/bin/env python3
"""Check pinned bytes or prepare a deterministic bundle and GitHub Release assets.

Uses PyYAML for authored package configuration. Semantic Blue validation is a separate command:
tools/verify_packages.py with the installed Blue Python implementation.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def wire(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode()


def local(root, name):
    path = root / name
    require(path.resolve().is_relative_to(root.resolve()), 'Path outside package home: ' + name)
    return path


def selections(root):
    catalogue = json.loads((root / 'PACKAGES.json').read_text())
    source = json.loads((root / 'PACKAGE-SOURCES.json').read_text())
    rows = catalogue['packages']
    require([r['directory'] for r in rows] == source['foundations'] + source['packages'],
            'Current catalogue differs from source inventory')
    require(len({r['name'] for r in rows}) == len(rows), 'Duplicate current package name')
    require(len({r['namespace'] for r in rows}) == len(rows), 'Duplicate current namespace')
    for row in rows:
        require(row['path'] == row['directory'] + '/dist/package.bluepkg'
                and '/' not in row['directory'], 'Package must live at the root')
        mount = catalogue['mounts'][row['namespace']]
        require(mount == dict(path=row['path'], blueId=row['packageBlueId'], archiveSha256=row['archiveSha256']),
                'Namespace mount differs from current package')
    require(set(catalogue['mounts']) == {r['namespace'] for r in rows}, 'Undeclared namespace mount')
    from sync_catalogues import sync
    sync(root, check=True)
    return [dict(row, selection='current') for row in rows]


def check_archive(root, row, *, retained=False):
    path = local(root, row['path'])
    data = path.read_bytes()
    require(digest(data) == row['archiveSha256'], 'Archive checksum differs: ' + row['name'])
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), 'Duplicate archive member: ' + row['name'])
        for name in names:
            require(not PurePosixPath(name).is_absolute() and '\\' not in name
                    and all(p not in ('', '.', '..') for p in name.split('/')),
                    'Unsafe archive member: ' + name)
        files = {name: archive.read(name) for name in names}
    manifest = json.loads(files['package.json'])
    require(manifest['packageBlueId'] == row['packageBlueId'], 'Manifest identity differs: ' + row['name'])
    require(set(files) == set(manifest['files']) | {'package.json'}, 'Archive inventory differs: ' + row['name'])
    for name, pin in manifest['files'].items():
        require(digest(files[name]) == pin['sha256'] and len(files[name]) == pin['size'],
                'Archive member differs: ' + row['name'] + '/' + name)
    if retained:
        for dependency in manifest['imports'].values():
            require(dependency['packageBlueId'] in manifest['semanticPackages'],
                    'Missing embedded retained dependency')
        return dict(row, name=manifest.get('name', row['name']), version=manifest['version'],
                    exports=manifest['exports'], imports={key: value['packageBlueId']
                    for key, value in manifest['imports'].items()},
                    protocolBlueId=manifest['protocol']), data
    # Every current publication retains its exact unpacked distribution for source checks.
    unpacked = {p.relative_to(path.parent).as_posix(): p.read_bytes()
                for p in path.parent.rglob('*') if p.is_file()}
    require(unpacked == {**files, 'package.bluepkg': data}, 'Unpacked distribution differs: ' + row['name'])
    closure = manifest['semanticPackages']
    for prefix, dependency in manifest['imports'].items():
        require(dependency['packageBlueId'] in closure,
                'Missing embedded dependency: ' + row['name'] + '/' + prefix)
    package_root = path.parent.parent
    lock = json.loads((package_root / 'blue-package.lock.json').read_text())
    for prefix, dependency in lock.get('imports', {}).items():
        dep_path = package_root / dependency['path']
        require(dep_path.resolve().is_relative_to(root.resolve()), 'Dependency outside package home')
        dep_data = dep_path.read_bytes()
        require(digest(dep_data) == dependency['archiveSha256'], 'Dependency checksum differs: ' + row['name'] + '/' + prefix)
        with zipfile.ZipFile(io.BytesIO(dep_data)) as archive:
            dep_manifest = json.loads(archive.read('package.json'))
        require(dep_manifest['packageBlueId'] == dependency['packageBlueId'], 'Dependency identity differs: ' + prefix)
        require(dependency['packageBlueId'] == manifest['imports'][prefix]['packageBlueId'],
                'Source lock differs from publication: ' + row['name'] + '/' + prefix)
    return dict(row, version=manifest['version'], exports=manifest['exports'],
                imports={name: pin['packageBlueId'] for name, pin in manifest['imports'].items()},
                protocolBlueId=manifest['protocol']), data


def retained_archives(root):
    """Validate explicitly pinned archive inputs, never active namespace mounts."""
    source = root / 'PACKAGE-SOURCES.json'
    pins = json.loads(source.read_text()).get('retainedArchives', []) if source.exists() else []
    result = {}
    identities = set()
    for pin in pins:
        require(set(pin) == {'path', 'packageBlueId', 'archiveSha256'}, 'Invalid retained archive pin')
        relative = PurePosixPath(pin['path'])
        require(not relative.is_absolute() and '\\' not in pin['path']
                and all(part not in ('', '.', '..') for part in pin['path'].split('/')),
                'Path outside package home: ' + pin['path'])
        path = local(root, pin['path']).resolve()
        require(path not in result and pin['packageBlueId'] not in identities, 'Duplicate retained archive pin')
        row, data = check_archive(root, dict(pin, name=pin['path'], selection='retained-data'), retained=True)
        result[path] = (row, data)
        identities.add(pin['packageBlueId'])
    return result


def retained_import(root, folder, prefix, declaration, config, retained):
    """Return an approved retained pin, rejecting execution use and pin drift."""
    path = (folder / declaration['path']).resolve()
    if path not in retained:
        return None
    require(prefix not in config.get('executionRequires', [])
            and prefix not in config.get('protocol', {}).get('requires', {}).values(),
            'Retained archive cannot be an execution requirement: ' + prefix)
    row = retained[path][0]
    for key in ('packageBlueId', 'archiveSha256'):
        if key in declaration:
            require(declaration[key] == row[key], 'Retained import pin differs: ' + prefix + '/' + key)
    return row


def check(root=ROOT):
    import yaml
    rows, payloads = [], {}
    current = selections(root)
    retained = retained_archives(root)
    selected_ids = {r['packageBlueId'] for r in current}
    require(not selected_ids.intersection(row['packageBlueId'] for row, _ in retained.values()),
            'Retained archive duplicates active publication')
    for selection in current:
        row, data = check_archive(root, selection)
        folder = root / selection['directory']
        config = yaml.safe_load((folder / 'blue-package.yaml').read_text())
        lock = json.loads((folder / 'blue-package.lock.json').read_text())
        for prefix, identity in row['imports'].items():
            pin = retained_import(root, folder, prefix, lock['imports'][prefix], config, retained)
            if identity not in selected_ids:
                require(pin is not None and pin['packageBlueId'] == identity,
                        'Dependency outside current catalogue: ' + row['name'])
                source_pin = retained_import(root, folder, prefix, config['imports'][prefix], config, retained)
                require(source_pin == pin, 'Retained source import differs: ' + prefix)
        rows.append(row)
        payloads[row['path']] = data
    indexed = {row['path'].removesuffix('/dist/package.bluepkg'): row for row in rows}
    for entry in json.loads((root / 'PACKAGES.json').read_text())['packages']:
        selected = indexed[entry['directory']]
        require(all(entry[key] == selected[key] for key in ('packageBlueId', 'archiveSha256')),
                'Release metadata differs: ' + entry['directory'])
    source_files = 0
    for name in ('blue-language', 'blue-bex', 'blue-contracts', 'blue-time'):
        folder = root / name
        for line in (folder / 'SHA256SUMS').read_text().splitlines():
            expected, relative = line.split(maxsplit=1)
            path = folder / relative.lstrip('*')
            require(path.resolve().is_relative_to(root.resolve()), 'Source inventory escapes package home')
            require(hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                    'Source checksum differs: ' + name + '/' + relative)
            source_files += 1
    for row, data in retained.values():
        rows.append(row)
        payloads[row['path']] = data
    return dict(format='blue-package-catalog/1', packages=rows,
                scope='Pinned archive integrity; semantic verification is separate.',
                sourceFilesChecked=source_files), payloads


def bundle(output, catalogue, payloads, root=ROOT):
    files = dict(payloads)
    files['CATALOG.json'] = wire(catalogue)
    files['README.md'] = (root / 'docs/distribution.md').read_bytes()
    files['THIRD-PARTY-NOTICES.md'] = (root / 'blue-language/THIRD-PARTY-NOTICES.md').read_bytes()
    files['SHA256SUMS'] = ''.join(
        hashlib.sha256(data).hexdigest() + '  ' + name + '\n'
        for name, data in sorted(files.items())).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects existing releases and selected source archives.
    with output.open('xb') as stream:
        try:
            with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                for name, data in sorted(files.items()):
                    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    info.create_system = 3
                    info.external_attr = 0o100644 << 16
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, data, compresslevel=9)
        except BaseException:
            output.unlink()
            raise
    return dict(path=str(output), archiveSha256=digest(output.read_bytes()), files=len(files))


def assets(output, catalogue, payloads, root=ROOT):
    """Prepare a flat upload directory, preserving each selected archive exactly."""
    require(set(payloads) == {row['path'] for row in catalogue['packages']},
            'Release payloads differ from catalogue')
    files = {
        'README.md': (root / 'docs/distribution.md').read_bytes(),
        'THIRD-PARTY-NOTICES.md': (root / 'blue-language/THIRD-PARTY-NOTICES.md').read_bytes(),
    }
    rows = []
    for row in catalogue['packages']:
        for key in ('name', 'version'):
            require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', row[key]) is not None,
                    'Unsafe release asset ' + key + ': ' + row[key])
        name = row['name'] + '-' + row['version'] + '.bluepkg'
        require(name not in files, 'Duplicate release asset: ' + name)
        data = payloads[row['path']]
        require(digest(data) == row['archiveSha256'], 'Release payload checksum differs: ' + name)
        files[name] = data
        rows.append(dict(row, releaseAsset=name))
    catalogue = dict(catalogue, packages=rows)
    files['CATALOG.json'] = wire(catalogue)
    # An exclusive directory prevents replacing any existing publication assets.
    output.mkdir(parents=True, exist_ok=False)
    try:
        for name, data in files.items():
            (output / name).write_bytes(data)
        result = bundle(output / 'blue-packages.zip', catalogue, payloads, root)
        files['blue-packages.zip'] = (output / 'blue-packages.zip').read_bytes()
        (output / 'SHA256SUMS').write_text(''.join(
            hashlib.sha256(data).hexdigest() + '  ' + name + '\n'
            for name, data in sorted(files.items())), encoding='utf-8')
    except BaseException:
        for path in output.iterdir():
            path.unlink()
        output.rmdir()
        raise
    return dict(path=str(output), files=len(files) + 1, bundle=result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('check', 'bundle', 'assets'))
    parser.add_argument('--output', type=Path)
    from editions import EDITIONS, edition_root, require_built
    parser.add_argument('--edition', choices=EDITIONS, default='access-events')
    args = parser.parse_args()
    selected = edition_root(ROOT, args.edition)
    require_built(selected)
    if (args.command != 'check') != (args.output is not None):
        parser.error('--output is required for bundle/assets and not allowed for check')
    catalogue, payloads = check(selected)
    result = dict(verified=True, packages=len(catalogue['packages']),
                  sourceFilesChecked=catalogue['sourceFilesChecked'],
                  publicationStatus='unpublished-candidate',
                  previewPackages=[r['name'] for r in catalogue['packages'] if 'preview' in r['version']])
    if args.command == 'bundle':
        result['bundle'] = bundle(args.output, catalogue, payloads, selected)
    elif args.command == 'assets':
        result['assets'] = assets(args.output, catalogue, payloads, selected)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
