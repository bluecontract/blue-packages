#!/usr/bin/env python3
"""Run reseller fixtures on native Contracts using an exact package set."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'examples/reseller/catalog.blue')
    parser.add_argument('--scenarios', type=Path, default=ROOT / 'examples/reseller/tests/catalog.case.json')
    parser.add_argument('--reseller-archive', type=Path,
                        help='Replay examples against an exact retained Reseller archive')
    parser.add_argument('--output', type=Path, default=ROOT / 'reports/reseller-20261103/catalog')
    args = parser.parse_args()
    classpath = os.environ.get('BLUE_JAVA_CLASSPATH')
    if not classpath:
        parser.error('Set BLUE_JAVA_CLASSPATH to the native Language/BEX/Contracts classes, dependencies and resources')
    catalogue_path = ROOT / 'retained/pre-declarative-reseller/PACKAGES.json'
    catalogue_bytes = catalogue_path.read_bytes()
    catalog = json.loads(catalogue_bytes)
    if args.reseller_archive is not None:
        retained = json.loads((ROOT / 'PACKAGE-SOURCES.json').read_text())['retainedArchives']
        archive = args.reseller_archive.resolve()
        pin = next((candidate for candidate in retained if ROOT / candidate['path'] == archive), None)
        if pin is None:
            parser.error('--reseller-archive must be pinned in PACKAGE-SOURCES.json')
        catalog['mounts']['Reseller'] = {
            'path': pin['path'], 'blueId': pin['packageBlueId'], 'archiveSha256': pin['archiveSha256']
        }
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    classes = output / 'classes'
    classes.mkdir(exist_ok=True)
    namespaces = {'Language', 'BEX', 'Contracts', 'Clauses', 'Connections', 'Money', 'Commerce',
                  'Activation', 'Agreements', 'Orders', 'Parties', 'Documents', 'Reseller', 'Amendments',
                  'PaymentInstruction', 'Payment', 'Features', 'Ledger', 'ManualPayments', 'MyOS', 'Events'}
    runtime = {'packages': [dict(namespace=namespace, path=str(ROOT / pin['path']),
                                packageBlueId=pin['blueId'], archiveSha256=pin['archiveSha256'])
                            for namespace, pin in catalog['mounts'].items() if namespace in namespaces],
               'evidence': {'catalogueSha256': 'sha256:' + hashlib.sha256(catalogue_bytes).hexdigest(),
                            'classpath': classpath, 'scope': 'Native component channels; no hosted identity, inventory or PSP claim'}}
    runtime_path = output / 'runtime.json'
    runtime_path.write_text(json.dumps(runtime, indent=2) + '\n')
    java_home = os.environ.get('JAVA_HOME')
    def java(name):
        return str(Path(java_home) / 'bin' / name) if java_home else name
    subprocess.run([java('javac'), '-cp', classpath, '-d', str(classes),
                    str(ROOT / 'tools/QualificationRuntime.java'),
                    str(ROOT / 'tools/ResellerScenarios.java')], check=True)
    subprocess.run([java('java'), '-Xmx2g', '-Dblue.contracts.hostGasLimit=10000000',
                    '-cp', str(classes) + os.pathsep + classpath, 'blue.packages.ResellerScenarios',
                    str(args.source.resolve()), str(args.scenarios.resolve()),
                    str(output / 'results.json'), str(runtime_path)], check=True)


if __name__ == '__main__':
    main()
