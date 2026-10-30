#!/usr/bin/env python3
"""Build one unpublished final-gas package with the maintained native Java builder.

Set BLUE_JAVA_CLASSPATH to the qualified Language runtime and its dependencies.
--check builds in isolation and compares every distribution byte, including the archive.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def dependency_order(root, names):
    """Build every declared dependency first, including currently inactive exports."""
    import yaml
    root = root.resolve()
    selected = set(names)
    complete, active, ordered = set(), set(), []

    def visit(name):
        if name in complete:
            return
        if name in active:
            raise ValueError('Package dependency cycle at ' + name)
        folder = root / name
        if folder.parent != root or name not in selected:
            raise ValueError('Dependency is absent from the source inventory: ' + name)
        active.add(name)
        config = yaml.safe_load((folder / 'blue-package.yaml').read_text())
        for declaration in config.get('imports', {}).values():
            archive = (folder / declaration['path']).resolve()
            dependency = archive.parent.parent
            if dependency.parent != root or archive != dependency / 'dist/package.bluepkg':
                # Retained editions are immutable leaves, never candidates to rebuild.
                retained = root / 'verification/publications'
                if (not archive.is_relative_to(retained) or not declaration.get('packageBlueId')
                        or not declaration.get('archiveSha256')):
                    raise ValueError('Unsupported package import path: ' + declaration['path'])
                digest = 'sha256:' + hashlib.sha256(archive.read_bytes()).hexdigest()
                if digest != declaration['archiveSha256']:
                    raise ValueError('Retained package integrity differs: ' + declaration['path'])
                continue
            visit(dependency.name)
        active.remove(name)
        complete.add(name)
        ordered.append(name)

    for name in names:
        visit(name)
    return ordered

def build(package, check=False):
    all_packages = package == 'all'
    if all_packages and check:
        raise ValueError('Use --check with one selected package')
    source = ROOT / ('blue-contracts' if all_packages else package)
    if source.parent != ROOT or not source.is_dir():
        raise ValueError('Select one package directory directly under the source root')
    classpath = os.environ.get('BLUE_JAVA_CLASSPATH')
    if not classpath:
        raise ValueError('Set BLUE_JAVA_CLASSPATH to the qualified Java Language runtime jars')
    home = os.environ.get('JAVA_HOME')
    java = str(Path(home) / 'bin/java') if home else 'java'
    javac = str(Path(home) / 'bin/javac') if home else 'javac'
    with tempfile.TemporaryDirectory(prefix='blue-final-gas-') as temporary:
        work = Path(temporary)
        classes = work / 'classes'
        classes.mkdir()
        subprocess.run([javac, '-cp', classpath, '-d', str(classes),
                        str(ROOT/'tools/OperationInputs.java'), str(ROOT/'tools/BuildPaymentFamily.java'), str(ROOT/'tools/BuildFinalGas.java')], check=True)
        selected = ROOT
        if check:
            selected = work / 'packages'
            selected.mkdir()
            shutil.copytree(source, selected/package, ignore=shutil.ignore_patterns('dist', '__pycache__', '.pytest_cache'))
            # Dependencies are pinned archives; preserve the manifest's relative paths.
            import yaml
            cfg = yaml.safe_load((source/'blue-package.yaml').read_text())
            for value in cfg['imports'].values():
                original = (source/value['path']).resolve()
                relative = original.relative_to(ROOT.resolve())
                destination = selected/relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(original, destination)
        names = [package]
        if all_packages:
            inventory = json.loads((ROOT/'PACKAGE-SOURCES.json').read_text())
            names = [name for name in dependency_order(ROOT, inventory['foundations'] + inventory['packages'])
                     if name != 'blue-language']
        for name in names:
            subprocess.run([java, '-Xmx1500m', '-cp', str(classes)+os.pathsep+classpath,
                            'BuildFinalGas', str(selected), name], check=True, stdout=subprocess.DEVNULL)
        if all_packages:
            subprocess.run([java, '-Xmx1500m', '-cp', str(classes)+os.pathsep+classpath,
                            'BuildPaymentFamily', str(ROOT), '__index_only__'], check=True)
            import sys
            subprocess.run([sys.executable,str(ROOT/'tools/sync_catalogues.py')],check=True)
        if check:
            def files(folder):
                return {p.relative_to(folder).as_posix():p.read_bytes() for p in folder.rglob('*') if p.is_file()}
            if files(selected/package/'dist') != files(source/'dist'):
                raise ValueError('Native rebuild differs from the selected distribution')
            if json.loads((selected/package/'blue-package.lock.json').read_text()) != json.loads((source/'blue-package.lock.json').read_text()):
                raise ValueError('Native rebuild differs from the dependency lock')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', help='One directory, or all to rebuild the candidate in dependency order')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    build(args.package, args.check)
