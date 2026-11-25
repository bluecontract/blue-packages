#!/usr/bin/env python3
"""Render an exact Go reseller fixture as commented, round-trip checked YAML."""
import argparse
from collections import defaultdict
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
from textwrap import wrap
from zipfile import ZipFile

import yaml


ORDER = ('orderTemplate',)
PAYMENT = ORDER + ('clauses', 'payment', 'parameters', 'template')
PAYOUT = ('payoutTemplate',)

ROLES = {
    (): {
        'activation': 'Sets the roles and approvals required for the current agreement terms.',
        'catalog': 'Prices the customer’s selection against the current catalog revision.',
        'quoteCommission': 'Sets the commission rate on first activation.',
        'orders': 'Prepares a separate Order and assigns it the current commission rate.',
        'receipts': 'Totals confirmed captures, refunds, and net receipts after refunds.',
        'commission': 'Updates the commission due using net receipts and the rate assigned to the Order.',
        'payouts': 'Prepares a separate Payment Instruction to pay the partner’s commission.',
        'catalogAmendments': 'Collects approval from both parties for a new catalog revision.',
        'commissionAmendments': 'Collects approval from both parties for a commission rate change.',
    },
    ORDER: {
        'activation': 'Sets Order roles and access and requires seller confirmation when configured.',
        'orderDecision': 'Specifies which activation operations are blocked after the seller rejects the Order.',
        'reservation': 'Handles reviewed reservation proposals and exposes the confirmed service time.',
        'windowStart': (
            'Records the first valid timestamp at the result path. '
            'If the value is absent, the window start is still unset.'
        ),
        'cancellation': 'Decides cancellation for the entire Order and emits Order Cancellation Accepted.',
        'payment': 'Prepares and attaches one Payment Instruction with the agreed amount, currency, and roles.',
    },
    PAYMENT: {
        'activation': 'Sets separate roles and access for the buyer, seller, and guarantor.',
        'method': 'Relays payment session and action events to the operator.',
        'payment': 'Issues native payment requests. The guarantor confirms the outcomes.',
        'securedTime': 'Records the time of the first full authorization and the secureFunds request ID.',
    },
    PAYOUT: {
        'activation': 'Sets roles and access separately for the commission payout instruction.',
        'payment': 'Requests the commission payout once the instruction’s conditions are met.',
        'method': 'Checks the transfer and records the operator’s charge and transfer references.',
    },
}

SECTION_ROLES = {
    ORDER: 'Separate customer Order document.',
    PAYMENT: 'Template for the separate customer Payment Instruction.',
    PAYOUT: 'Template for the separate commission payout instruction.',
}


def digest(data):
    return sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def archive_aliases(root, catalogue):
    aliases = defaultdict(set)
    for row in json.loads(catalogue)['packages']:
        path = root / row['path']
        archive_bytes = path.read_bytes()
        if row['archiveSha256'] != 'sha256:' + digest(archive_bytes):
            raise ValueError(f'Archive SHA does not match the catalogue for {row["name"]}')
        with ZipFile(BytesIO(archive_bytes)) as archive:
            manifest = json.loads(archive.read('package.json'))
        if row['packageBlueId'] != manifest['packageBlueId']:
            raise ValueError(f'Archive BlueId does not match the catalogue for {row["name"]}')
        for exported in manifest['exports']:
            aliases[exported['blueId']].add(exported['alias'])
    return aliases


def role_comments(source, aliases):
    comments = dict(SECTION_ROLES)
    for path, roles in ROLES.items():
        section = source
        for key in path:
            section = section[key]
        if path == ORDER and 'orderOpen' in section.get('contracts', {}):
            comments[path + ('contracts', 'orderOpen')] = (
                'The Order type enforces closure rules. This configuration supplies the cancellation state '
                'and any reservation actions configured for the offer.'
            )
        for clause in (section, *section['clauses'].values()):
            declared = clause.get('type')
            if isinstance(declared, dict) and set(declared) == {'blueId'} and declared['blueId'] not in aliases:
                raise ValueError(f'Unknown mounted exact type at {path}: {declared["blueId"]}')
        for name, clause in section['clauses'].items():
            text = roles[name]
            bindings = clause.get('bindings', {})
            if path == () and name == 'catalogAmendments' and clause.get('parameters', {}).get('replacementValidator'):
                text += ' The referenced Commerce function compares the current and proposed catalogs.'
            if path == ORDER and name == 'activation' and clause.get('parameters', {}).get('reviewedApprovals'):
                text += (
                    ' Activation checks the signed event for the selected reservation '
                    'and approves the terms for the specified role.'
                )
            if path == ORDER and name == 'activation' and any(
                grant.get('observations')
                for grant in clause.get('parameters', {}).get('preActivationConnections', [])
            ):
                comments[path + ('clauses', name, 'parameters', 'preActivationConnections')] = (
                    'A single entry lets the action refresh cancellation availability before activation. '
                    'It covers automatic refresh and the observations declared by the action.'
                )
            if path == ORDER and name == 'reservation':
                text += ' After approval of the exact version, it emits Reservation Reviewed for that group.'
            if path == ORDER and name == 'windowStart' and 'unavailable' in bindings:
                text += (
                    ' If the activation time is reported missing, '
                    'the selected instruction can supply the time of full authorization.'
                )
            if path == PAYMENT and name == 'payment':
                parameters = clause.get('parameters', {})
                adjustments = parameters.get('adjustments', {})
                if 'cancellation' in adjustments:
                    text += (
                        ' The linked decision sets the amount to retain. '
                        'The instruction can request a refund or release the hold.'
                    )
                elif 'rejection' in adjustments:
                    text += ' Order rejection can trigger a request to release the authorization.'
                if 'selectedPayment' in parameters:
                    comments[path + ('clauses', name, 'parameters', 'selectedPayment')] = (
                        'Links the Order and its selected instruction for the adjustment rules.'
                    )
                if 'afterPaymentSelected' in bindings.get('adjust', {}):
                    comments[path + ('clauses', name, 'bindings', 'adjust', 'afterPaymentSelected')] = (
                        'After this instruction is selected, checks for an earlier decision, such as cancellation '
                        'while payment was pending, and can release an existing hold.'
                    )
                if 'method' not in parameters and 'method' in section.get('paymentDetails', {}):
                    comments[path + ('paymentDetails', 'method')] = 'The single setting for the customer’s payment method.'
            comments[path + ('clauses', name)] = text
    return comments


def annotate(node, aliases, comments, lines, path=()):
    if isinstance(node, yaml.SequenceNode):
        for index, child in enumerate(node.value):
            yield from annotate(child, aliases, comments, lines, path + (index,))
        return
    if isinstance(node, yaml.MappingNode):
        for key, child in node.value:
            if not isinstance(key, yaml.ScalarNode):
                continue
            here = path + (key.value,)
            if here in comments:
                prefix = ' ' * key.start_mark.column + '# '
                yield key.start_mark.line, [prefix + part for part in wrap(comments[here], 118 - len(prefix))]
            if key.value == 'blueId' and path[-1:] == ('type',) and isinstance(child, yaml.ScalarNode):
                names = aliases.get(child.value)
                if names:
                    lines[key.start_mark.line] += '  # ' + ', '.join(sorted(names))
            yield from annotate(child, aliases, comments, lines, here)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Exact Go source as JSON or a tracked .blue fixture')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    source_bytes = args.source.read_bytes()
    source = json.loads(source_bytes)
    catalogue = (root / 'PACKAGES.json').read_bytes()
    aliases = archive_aliases(root, catalogue)
    roles = role_comments(source, aliases)
    body = yaml.safe_dump(source, allow_unicode=True, sort_keys=False, width=110)
    lines = body.splitlines()
    comments = dict(annotate(yaml.compose(body, Loader=yaml.SafeLoader), aliases, roles, lines))
    if len(comments) != len(roles):
        raise ValueError('A required role comment could not be placed')
    header = [
        '# ' + source['name'],
        '# Comments show package aliases next to their exact BlueIds.',
        '# Source SHA-256: ' + digest(source_bytes),
        '# Catalogue SHA-256: ' + digest(catalogue),
        '# Document SHA-256 (canonical JSON): ' + digest(canonical(source)),
        '',
    ]
    for index, line in enumerate(lines):
        header.extend(comments.get(index, ()))
        header.append(line)
    rendered = '\n'.join(header) + '\n'
    if canonical(yaml.safe_load(rendered)) != canonical(source):
        raise ValueError('The annotated YAML differs from the exact Go source')
    sys.stdout.write(rendered)


if __name__ == '__main__':
    main()
