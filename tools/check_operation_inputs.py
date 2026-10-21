#!/usr/bin/env python3
"""Qualify current native operation inputs against an explicitly supplied Core classpath.

No package publication, network calls, production documents or model calls occur.
Run after building the complete candidate. All results identify the exact catalogue.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    'helper-native': ('OperationInputConformance', 'native'),
    'helper-payment': ('OperationInputConformance', 'payment'),
    'helper-final': ('OperationInputConformance', 'final'),
    'activation-inputs': ('OperationCatalogConformance', 'activation-complete'),
    'activation-effects': ('ActivationExecutionConformance',),
    'shipping': ('OperationCatalogConformance', 'shipping'),
    'payment-inputs': ('PaymentInputConformance',),
    'payment-effects': ('blue.core.PaymentExecutionConformance',),
    'providers': ('ProviderInputConformance', 'all'),
    'actions': ('ActionInputConformance',),
    **{'documents-' + mode: ('DocumentInputConformance', mode)
       for mode in ('source', 'inputs', 'consent', 'access', 'reference', 'representation', 'connection', 'preparation', 'accessGuards', 'paymentPreparation')},
    'configured-actions': ('blue.core.CurrentOperationScenarios', '07', '15', '16', '18', '20', '25'),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', action='append', choices=CASES)
    parser.add_argument('--report-dir', type=Path, default=ROOT / 'reports/operation-input/qualification',
                        help='Separate evidence directory for a qualification run')
    args = parser.parse_args()
    classpath = os.environ.get('BLUE_JAVA_CLASSPATH')
    if not classpath:
        parser.error('BLUE_JAVA_CLASSPATH must identify the qualified native Core runtime')
    java_home = os.environ.get('JAVA_HOME')
    java = str(Path(java_home) / 'bin/java') if java_home else 'java'
    javac = str(Path(java_home) / 'bin/javac') if java_home else 'javac'
    report_dir = args.report_dir.resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    selected = args.case or list(CASES)
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z'], cwd=ROOT).split(b'\0')
    report = {
        'catalogueSha256': hashlib.sha256((ROOT / 'PACKAGES.json').read_bytes()).hexdigest(),
        'packages': json.loads((ROOT / 'PACKAGES.json').read_text())['packages'],
        'runtimeClasspath': classpath.split(os.pathsep),
        'sourceHead': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'sourceUntrackedSha256': {name.decode(): hashlib.sha256((ROOT / name.decode()).read_bytes()).hexdigest()
                                 for name in untracked if name and (ROOT / name.decode()).is_file()},
        'sourceDirtyDiffSha256': hashlib.sha256(subprocess.check_output(['git', 'diff', '--binary', 'HEAD'], cwd=ROOT)).hexdigest(),
        'cases': [],
    }
    sources = {'OperationInputs', 'BuildPaymentFamily', 'BuildFinalGas', 'OperationInputConformance'}
    for key in selected:
        sources.add(CASES[key][0].split('.')[-1])
    if {'ActivationExecutionConformance', 'DocumentInputConformance'} & sources:
        sources.add('OperationCatalogConformance')
    if 'PaymentExecutionConformance' in sources:
        sources.add('CurrentOperationScenarios')
    with tempfile.TemporaryDirectory(prefix='operation-input-qualification-') as classes:
        subprocess.run([javac, '-cp', classpath, '-d', classes,
                        *[str(ROOT / 'tools' / (name + '.java')) for name in sorted(sources)]], check=True)
        for key in selected:
            name, *arguments = CASES[key]
            argv = ([*arguments, str(ROOT)] if name == 'OperationInputConformance'
                    else [str(ROOT), *arguments])
            command = [java, '-Xmx1500m', '-cp', classes + os.pathsep + classpath, name, *argv]
            start = time.monotonic()
            with (report_dir / (key + '.log')).open('w') as log:
                result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            row = {'id': key, 'command': command, 'status': 'PASS' if result.returncode == 0 else 'FAIL',
                   'exitCode': result.returncode, 'seconds': round(time.monotonic() - start, 3),
                   'log': str(report_dir / (key + '.log'))}
            report['cases'].append(row)
            (report_dir / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
            print(key + ': ' + row['status'], flush=True)
    return 0 if all(row['status'] == 'PASS' for row in report['cases']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
