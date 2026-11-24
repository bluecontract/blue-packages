#!/usr/bin/env python3
"""Qualify current native operation inputs against an explicitly supplied Core classpath.

No package publication, network calls, production documents or model calls occur.
Run after building the complete candidate. All results identify the exact catalogue.
"""
import argparse
import hashlib
import json
import os
import secrets
from pathlib import Path
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    'myos-instruction-types': ('blue.core.MyosInstructionTypesConformance',),
    'access-events-behavior': ('blue.core.AccessEventsConformance',),
    'helper-native': ('OperationInputConformance', 'native'),
    'helper-payment': ('OperationInputConformance', 'payment'),
    'helper-final': ('OperationInputConformance', 'final'),
    'activation-inputs': ('OperationCatalogConformance', 'activation-complete'),
    'representative-access': ('RepresentativeAccessConformance',),
    'activation-effects': ('ActivationExecutionConformance',),
    'activation-connection-references': ('ActivationConnectionReferencesConformance',),
    'source-path-declarations': ('SourcePathsDeclarationConformance',),
    'source-path-observation': ('SourcePathsObservationConformance',),
    **{'source-path-' + mode: ('SourcePathsObservationConformance', mode)
       for mode in ('admission', 'collision', 'undeclared', 'foreign-source', 'nonroot', 'escaped-alias')},
    'source-binding': ('SourceBindingConformance',),
    'source-binding-cyclic': ('SourceBindingConformance', 'cyclic'),
    'source-binding-public': ('SourceBindingConformance', 'public', 'cyclic'),
    'source-binding-history': ('SourceBindingConformance', 'cyclic', 'history'),
    'source-binding-replay': ('SourceBindingConformance', 'cyclic', 'replay'),
    'source-binding-guards': ('SourceBindingConformance', 'guards'),
    'source-binding-routing': ('SourceBindingConformance', 'routing'),
    'document-provision': ('ProvisionInputConformance',),
    'bootstrap-preparation': ('BootstrapPreparationConformance',),
    'declarative-commerce': ('BaseCommerceConformance',),
    'whole-order-cancellation': ('WholeOrderCancellationConformance',),
    'schedule-reservation': ('ScheduleReservationConformance',),
    'declarative-order-preparation': ('blue.core.DeclarativeOrderPreparationConformance',),
    'declarative-timed-payment-init': ('blue.core.CatalogOrderAttachmentConformance',
                                       'examples/sales/declarative/timed-bicycle-rental-agreement.blue',
                                       'timed-typed-pi-init'),
    'declarative-order-decision': ('OrderDecisionConformance',),
    'declarative-receipts': ('DeclarativeReceiptsConformance',),
    'declarative-account-payouts': ('blue.core.CommissionPayoutConformance', '--declarative'),
    'declarative-stripe-payout-preparation': ('blue.core.CommissionPayoutConformance', '--declarative-stripe-preparation'),
    'reseller-catalog-capacity': ('CatalogCapacityConformance',),
    'reseller-catalog-order-attachment': ('blue.core.CatalogOrderAttachmentConformance',),
    'reseller-catalog-order-independent': ('blue.core.CatalogOrderIndependentConformance',),
    'reseller-catalog-order-converged-source': ('blue.core.CatalogOrderIndependentConformance', 'converged-source'),
    'refresh-definition': ('RefreshDefinitionConformance',),
    'admission-consent-declarations': ('AdmissionConsentDeclarationConformance',),
    'admission-provision': ('AdmissionProvisionConformance',),
    'admission-planner': ('ProvidedOrderAdmissionConformance',),
    'admission-definition': ('AdmissionDefinitionConformance',),
    'static-identity-predicate': ('StaticIdentityPredicateConformance',),
    'connections-automatic': ('OperationCatalogConformance', 'automatic'),
    'connections-condition-groups': ('ConnectionConditionGroupsConformance',),
    'shipping': ('OperationCatalogConformance', 'shipping'),
    'payment-inputs': ('PaymentInputConformance',),
    'payment-effects': ('blue.core.PaymentExecutionConformance',),
    'providers': ('ProviderInputConformance', 'all'),
    'actions': ('ActionInputConformance',),
    **{'documents-' + mode: ('DocumentInputConformance', mode)
       for mode in ('source', 'inputs', 'consent', 'access', 'reference', 'representation', 'connection', 'preparation', 'accessGuards', 'paymentPreparation', 'attachmentValues', 'documentPreparationFields', 'documentPreparationValues')},
    'configured-actions': ('blue.core.CurrentOperationScenarios', '07', '13', '14', '15', '16', '18', '20', '25'),
    'current-payment-obligations': ('blue.core.CurrentOperationScenarios', '31', '32'),
    'two-payment-provisions': ('blue.core.TwoPaymentObligationsConformance',),
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
    # The independent checkout uses Core's PostgreSQL test host and is opt-in.
    independent_cases = {'reseller-catalog-order-independent', 'reseller-catalog-order-converged-source'}
    selected = args.case or [case for case in CASES if case not in independent_cases]
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z'], cwd=ROOT).split(b'\0')
    report = {
        'edition': 'access-events',
        'catalogueSha256': hashlib.sha256((ROOT / 'PACKAGES.json').read_bytes()).hexdigest(),
        'packages': json.loads((ROOT / 'PACKAGES.json').read_text())['packages'],
        'runtimeClasspath': classpath.split(os.pathsep),
        'sourceHead': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'sourceUntrackedSha256': {name.decode(): hashlib.sha256((ROOT / name.decode()).read_bytes()).hexdigest()
                                 for name in untracked if name and (ROOT / name.decode()).is_file()},
        'sourceDirtyDiffSha256': hashlib.sha256(subprocess.check_output(['git', 'diff', '--binary', 'HEAD'], cwd=ROOT)).hexdigest(),
        'cases': [],
    }
    sources = {'QualificationRuntime', 'OperationInputs', 'BuildPaymentFamily', 'BuildFinalGas', 'OperationInputConformance'}
    for key in selected:
        sources.add(CASES[key][0].split('.')[-1])
    if 'DeclarativeOrderPreparationConformance' in sources:
        sources.add('CommissionPayoutConformance')
    if {'DeclarativeReceiptsConformance', 'SourcePathsDeclarationConformance', 'SourcePathsObservationConformance', 'AdmissionDefinitionConformance', 'RefreshDefinitionConformance', 'AdmissionProvisionConformance', 'ProvidedOrderAdmissionConformance'} & sources:
        sources.add('BootstrapPreparationConformance')
    if {'StaticIdentityPredicateConformance', 'AdmissionProvisionConformance'} & sources:
        sources.add('AdmissionConsentDispatchConformance')
    if {'ActivationExecutionConformance', 'DocumentInputConformance'} & sources:
        sources.add('OperationCatalogConformance')
    if {'PaymentExecutionConformance', 'MyosInstructionTypesConformance', 'TwoPaymentObligationsConformance'} & sources:
        sources.add('CurrentOperationScenarios')
    if independent_cases.intersection(selected):
        sources.update({'CatalogOrderIndependentGuarantor', 'CatalogOrderIndependentMandates',
                        'CatalogOrderIndependentPrecheckout'})
    with tempfile.TemporaryDirectory(prefix='operation-input-qualification-') as classes:
        subprocess.run([javac, '-cp', classpath, '-d', classes,
                        *[str(ROOT / 'tools' / (name + '.java')) for name in sorted(sources)]], check=True)
        for key in selected:
            name, *arguments = CASES[key]
            argv = ([*arguments, str(ROOT)] if name == 'OperationInputConformance'
                    else [str(ROOT), *arguments])
            case_workdir = ROOT
            case_classpath = classes + os.pathsep + classpath
            java_options = ['-Xmx1500m']
            environment = None
            if key in independent_cases:
                case_workdir = report_dir / 'runtime'
                case_workdir.mkdir(exist_ok=True)
                case_classpath += os.pathsep + str(ROOT)
                java_options = ['-Xmx4500m', '-Dblue.core.selectedRegistrations=true']
                environment = {name: value for name, value in os.environ.items()
                               if not name.startswith(('CORE_', 'BLUE_DYNAMODB'))}
                master_key = Path(classes) / (key + '.key')
                with os.fdopen(os.open(master_key, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as key_file:
                    key_file.write(secrets.token_bytes(32))
                environment.update({
                    'CORE_ROLE': 'standalone',
                    'CORE_BIND': '127.0.0.1',
                    'PORT': '0',
                    'CORE_DATA': str(Path(classes) / key),
                    'CORE_MASTER_KEY_FILE': str(master_key),
                    'CORE_TIMELINE_PROVIDER_ENDPOINT': 'https://paid-reseller.example.test/provider',
                    'CORE_PAYMENT_GUARANTOR_ACCOUNT_ID': 'guarantor',
                })
            command = [java, *java_options, '-cp', case_classpath, name, *argv]
            start = time.monotonic()
            with (report_dir / (key + '.log')).open('w') as log:
                result = subprocess.run(command, cwd=case_workdir, env=environment, stdout=log, stderr=subprocess.STDOUT)
            row = {'id': key, 'command': command, 'status': 'PASS' if result.returncode == 0 else 'FAIL',
                   'exitCode': result.returncode, 'seconds': round(time.monotonic() - start, 3),
                   'log': str(report_dir / (key + '.log'))}
            if key == 'reseller-catalog-order-attachment':
                selection = ROOT / 'retained/pre-declarative-reseller/PACKAGES.json'
                row['cataloguePath'] = str(selection.relative_to(ROOT))
                row['catalogueSha256'] = hashlib.sha256(selection.read_bytes()).hexdigest()
            report['cases'].append(row)
            (report_dir / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
            print(key + ': ' + row['status'], flush=True)
    return 0 if all(row['status'] == 'PASS' for row in report['cases']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
