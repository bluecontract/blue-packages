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
        'activation': 'Ustala wymagane role i zatwierdzenia aktualnych warunków umowy.',
        'catalog': 'Wycenia wybór klienta na aktualnej rewizji katalogu.',
        'quoteCommission': 'Ustala obowiązującą stawkę prowizji przy pierwszej aktywacji.',
        'orders': 'Przygotowuje osobne zamówienie i przypisuje mu obowiązującą stawkę prowizji.',
        'receipts': 'Sumuje potwierdzone pobrania, zwroty i wpływy po zwrotach.',
        'commission': 'Aktualizuje należną prowizję z wpływów i przypisanej stawki zamówienia.',
        'payouts': 'Przygotowuje oddzielną instrukcję wypłaty prowizji partnerowi.',
        'catalogAmendments': 'Zbiera zatwierdzenia obu stron dla nowej rewizji katalogu.',
        'commissionAmendments': 'Zbiera zatwierdzenia obu stron dla zmiany stawki prowizji.',
    },
    ORDER: {
        'activation': 'Ustala role i dostęp zamówienia oraz wymaga potwierdzenia sprzedawcy, gdy jest skonfigurowane.',
        'orderDecision': 'Wskazuje operacje aktywacji blokowane po odrzuceniu zamówienia przez sprzedawcę.',
        'reservation': 'Obsługuje zweryfikowane propozycje rezerwacji i udostępnia potwierdzony termin usługi.',
        'windowStart': 'Zapamiętuje pierwszy prawidłowy czas w ścieżce result. Brak wartości oznacza, że początek okna nie został jeszcze zapisany.',
        'cancellation': 'Rozstrzyga anulowanie całego zamówienia i emituje Order Cancellation Accepted.',
        'payment': 'Przygotowuje i dołącza jedną instrukcję płatności z uzgodnioną kwotą, walutą i rolami.',
    },
    PAYMENT: {
        'activation': 'Oddzielnie ustala role i dostęp kupującego, sprzedawcy i gwaranta.',
        'method': 'Przekazuje operatorowi zdarzenia sesji i dyspozycji płatniczych.',
        'payment': 'Składa natywne dyspozycje płatnicze. Gwarant potwierdza wyniki.',
        'securedTime': 'Zapisuje czas pierwszej pełnej autoryzacji i identyfikator żądania secureFunds.',
    },
    PAYOUT: {
        'activation': 'Oddzielnie ustala role i dostęp do instrukcji wypłaty prowizji.',
        'payment': 'Zleca wypłatę prowizji po spełnieniu warunków instrukcji.',
        'method': 'Sprawdza przelew i zapisuje referencje obciążenia i przelewu od operatora.',
    },
}

SECTION_ROLES = {
    ORDER: 'Osobny dokument zamówienia klienta.',
    PAYMENT: 'Szablon osobnej instrukcji płatności klienta.',
    PAYOUT: 'Szablon osobnej instrukcji wypłaty prowizji.',
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
                'Typ zamówienia stosuje reguły zamknięcia. Tutaj podajemy stan anulowania '
                'i akcje rezerwacji, jeśli występują w tej ofercie.'
            )
        for clause in (section, *section['clauses'].values()):
            declared = clause.get('type')
            if isinstance(declared, dict) and set(declared) == {'blueId'} and declared['blueId'] not in aliases:
                raise ValueError(f'Unknown mounted exact type at {path}: {declared["blueId"]}')
        for name, clause in section['clauses'].items():
            text = roles[name]
            bindings = clause.get('bindings', {})
            if path == () and name == 'catalogAmendments' and clause.get('parameters', {}).get('replacementValidator'):
                text += ' Wskazana funkcja Commerce porównuje bieżący i proponowany katalog.'
            if path == ORDER and name == 'activation' and clause.get('parameters', {}).get('reviewedApprovals'):
                text += ' Activation sprawdza podpisane zdarzenie wybranej rezerwacji i zatwierdza warunki wskazanej roli.'
            if path == ORDER and name == 'activation' and any(
                grant.get('observations')
                for grant in clause.get('parameters', {}).get('preActivationConnections', [])
            ):
                comments[path + ('clauses', name, 'parameters', 'preActivationConnections')] = (
                    'Jeden wpis pozwala akcji odświeżać dostępność anulowania przed aktywacją. '
                    'Obejmuje automatyczne odświeżenie i obserwacje zadeklarowane przez akcję.'
                )
            if path == ORDER and name == 'reservation':
                text += ' Po zatwierdzeniu dokładnej wersji emituje zdarzenie Reservation Reviewed dla tej grupy.'
            if path == ORDER and name == 'windowStart' and 'unavailable' in bindings:
                text += ' Po zgłoszeniu braku czasu aktywacji można odczytać pełną autoryzację wybranej instrukcji.'
            if path == PAYMENT and name == 'payment':
                parameters = clause.get('parameters', {})
                adjustments = parameters.get('adjustments', {})
                if 'cancellation' in adjustments:
                    text += ' Powiązana decyzja wyznacza kwotę zatrzymaną. Instrukcja może zlecić zwrot lub zwolnienie blokady.'
                elif 'rejection' in adjustments:
                    text += ' Odrzucenie zamówienia może zlecić zwolnienie autoryzacji.'
                if 'selectedPayment' in parameters:
                    comments[path + ('clauses', name, 'parameters', 'selectedPayment')] = (
                        'Wspólne wskazanie zamówienia i jego wybranej instrukcji dla reguł korekty.'
                    )
                if 'afterPaymentSelected' in bindings.get('adjust', {}):
                    comments[path + ('clauses', name, 'bindings', 'adjust', 'afterPaymentSelected')] = (
                        'Po wyborze tej instrukcji sprawdza wcześniejszą decyzję, np. anulowanie '
                        'podczas oczekiwania na płatność, i może zwolnić istniejącą blokadę.'
                    )
                if 'method' not in parameters and 'method' in section.get('paymentDetails', {}):
                    comments[path + ('paymentDetails', 'method')] = 'Jedno ustawienie metody płatności klienta.'
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
        '# Nazwy pakietowe podano w komentarzach obok dokładnych identyfikatorów Blue.',
        '# SHA-256 źródła: ' + digest(source_bytes),
        '# SHA-256 katalogu: ' + digest(catalogue),
        '# SHA-256 dokumentu (kanoniczny JSON): ' + digest(canonical(source)),
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
