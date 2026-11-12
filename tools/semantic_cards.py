#!/usr/bin/env python3
"""Check, prepare, generate, import or publish exact public semantic cards."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import tempfile

from jsonschema import Draft202012Validator

from release import ROOT, digest, local, require, wire
from semantic_sources import context_wire, definition_digest, evidence, inventory, pointer
from semantic_s3 import MAX_CARD_BYTES, Store, card_key

ASSETS = Path(__file__).resolve().parents[1] / 'semantics'
OUTPUT_SCHEMA = json.loads((ASSETS / 'output.schema.json').read_text())
GENERATED_VALIDATOR = Draft202012Validator(OUTPUT_SCHEMA)
# Existing public cards may predate metadata or explicit fact scope/aggregate.
STORED_SCHEMA = deepcopy(OUTPUT_SCHEMA)
STORED_SCHEMA['required'].remove('metadata')
for key in ('scope', 'path', 'aggregate'):
    STORED_SCHEMA['properties']['metadata']['properties']['stateFacts']['items']['required'].remove(key)
VALIDATOR = Draft202012Validator(STORED_SCHEMA)


def read_json(path, limit=MAX_CARD_BYTES):
    require(not path.is_symlink(), 'Symlink is not a semantic artifact: ' + str(path))
    require(path.stat().st_size <= limit, 'Semantic artifact exceeds its size limit: ' + str(path))
    return json.loads(path.read_bytes())


def validate_output(value, context=None):
    (GENERATED_VALIDATOR if context is not None else VALIDATOR).validate(value)
    if 'metadata' in value:
        require(len(wire(value['metadata'])) <= 16_384, 'State metadata exceeds the byte limit')
    title, _, body = value['semanticText'].strip().partition('\n')
    require(title.startswith('# ') and title[2:].strip(), 'Card text needs a heading')
    require(body.strip(), 'Card text needs an explanation')
    require(len(value['semanticText'].encode()) <= 48_000, 'Card text exceeds the byte limit')
    if context is not None:
        require(value['blueId'] == context['blueId'], 'Generated BlueId differs from source')
        validate_metadata(value['metadata'], context)


def validate_metadata(metadata, context):
    require(set(metadata['parameterRefs']) <= set(context['parameterRefs']),
            'Metadata parameter reference is not declared by the source')
    for key in ('covers', 'dependencies'):
        require(set(metadata[key]) <= set(context['referencedBlueIds']),
                'Metadata ' + key + ' includes an unreferenced type')
    bindings = {b['name']: b['defaultPath'] for b in context['bindings']}
    ids = set()
    for fact in metadata['stateFacts']:
        require(fact['id'] not in ids, 'Duplicate state fact: ' + fact['id'])
        ids.add(fact['id'])
        if fact['scope'] == 'binding':
            require(fact['path'] is None and fact['binding'] in bindings
                    and fact['defaultPath'] == bindings[fact['binding']],
                    'State fact binding/default differs from the source: ' + fact['id'])
            require(fact['suffix'] == '' or pointer(fact['suffix']), 'Invalid state fact suffix')
        else:
            require(fact['binding'] is None and fact['defaultPath'] is None and fact['suffix'] == '',
                    'Document/clause facts cannot use a binding or suffix')
            path = fact['path']
            if fact['scope'] == 'document':
                require(pointer(path) and path in context['documentPaths'],
                        'State fact document path is not established by the source: ' + str(path))
            else:
                require(pointer(path) and any(path == base or path.startswith(base + '/')
                        for base in context.get('clausePaths', [])),
                        'State fact clause path is not established by the source: ' + str(path))
        require(fact['aggregate'] is None or fact['type'] in {'number', 'count', 'money-minor'},
                'State fact aggregate requires a numeric type')


def validate_card(card, blue_id):
    validate_output(card)
    require(card['blueId'] == blue_id, 'Card filename/BlueId mismatch')
    require(len(wire(card)) <= MAX_CARD_BYTES, 'Card exceeds stored byte limit')
    return card


def cards_in(root):
    require(not (root / 'semantics').is_symlink() and not (root / 'semantics/cards').is_symlink(),
            'Semantic directories cannot be symlinks')
    folder = local(root, 'semantics/cards')
    cards = {}
    for path in sorted(folder.glob('*.json')):
        cards[path.stem] = validate_card(read_json(path), path.stem)
    return cards


def save_card(folder, card):
    require(not folder.is_symlink() and not folder.parent.is_symlink(), 'Semantic directories cannot be symlinks')
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (card['blueId'] + '.json')
    data = wire(card)
    if path.exists():
        require(not path.is_symlink() and path.read_bytes() == data, 'Refusing to replace an existing card: ' + card['blueId'])
    else:
        with path.open('xb') as stream:
            stream.write(data)


def prepare(root, output, store=None, refresh=()):
    subjects, definitions = inventory(root)
    require(set(refresh) <= subjects.keys(), 'Refresh identity is outside the selected sources')
    require(len(set(refresh)) <= 256, 'Refresh is limited to 256 exact identities per run')
    cards = cards_in(root)
    keys = store.keys() if store else set()
    restored = []
    for blue_id in subjects.keys() - cards.keys() - set(refresh):
        card = store.restore(blue_id, keys) if store else None
        if card is not None:
            validate_card(card, blue_id)
            staged = output / 'cards' / (blue_id + '.json')
            require(not staged.is_symlink() and not staged.parent.is_symlink(), 'Semantic cache cannot be a symlink')
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(wire(card))
            cards[blue_id] = card
            restored.append(blue_id)
    missing = sorted(subjects.keys() - cards.keys())
    generator = json.loads((ASSETS / 'generator.json').read_text())
    prompt = (ASSETS / 'prompt.md').read_text()
    generator['promptSha256'] = digest(prompt.encode())
    generator['schemaSha256'] = digest(wire(OUTPUT_SCHEMA))
    output.mkdir(parents=True, exist_ok=True)
    requests = output / 'requests'
    requests.mkdir(exist_ok=True)
    # GitHub matrices allow at most 256 jobs. A committed batch triggers the next
    # coverage run, which discovers the remaining IDs without regenerating these.
    batch = sorted(set(refresh)) if refresh else missing[:256]
    for blue_id in batch:
        context = evidence(blue_id, definitions)
        request = dict(context=context, definitionDigest=definition_digest(blue_id, definitions),
                       sourceDigest=digest(context_wire(context)), package=subjects[blue_id]['package'], generator=generator)
        (requests / (blue_id + '.json')).write_bytes(wire(request))
        (requests / (blue_id + '.txt')).write_text(prompt + '\n\nEvidence (JSON):\n' + context_wire(context).decode('utf-8'), encoding='utf-8')
    report = dict(format='blue-semantic-plan/1', subjects=list(subjects.values()),
                  ready=sorted(subjects.keys() & cards.keys()), restored=sorted(restored), missing=missing,
                  generate=batch, refresh=sorted(set(refresh)),
                  unpublished=sorted(id for id in cards if store and card_key(id) not in keys),
                  remoteChecked=store is not None, generator=generator)
    (output / 'plan.json').write_bytes(wire(report))
    return report


def accept(request, response, output, definitions=None):
    context = request['context']
    require(request['sourceDigest'] == digest(context_wire(context)), 'Generation request checksum mismatch')
    if definitions is not None:
        require(context['blueId'] in definitions, 'Generation source is outside current selection')
        require(request['definitionDigest'] == definition_digest(context['blueId'], definitions),
                'Generation definition digest mismatch')
        require(request['sourceDigest'] == digest(context_wire(evidence(context['blueId'], definitions))),
                'Generation evidence differs from current source')
    validate_output(response, context)
    validate_card(response, context['blueId'])
    save_card(output, response)
    return response


def generate(root, output, jobs, store=None, refresh=()):
    plan = prepare(root, output, store, refresh)
    destination = local(root, 'semantics/cards')
    for blue_id in plan['restored']:
        save_card(destination, read_json(output / 'cards' / (blue_id + '.json')))
    if not plan['generate']:
        return plan
    # Refresh candidates are reviewed before replacing a published local card.
    if refresh:
        destination = output / 'cards'
    version = subprocess.check_output(['codex', '--version'], text=True).strip()
    require(version == 'codex-cli ' + plan['generator']['codexVersion'], 'Install the pinned Codex CLI version from semantics/generator.json')

    def one(blue_id):
        if (destination / (blue_id + '.json')).exists():
            require(not refresh, 'Refresh candidate already exists; use a new output directory: ' + blue_id)
            validate_card(read_json(destination / (blue_id + '.json')), blue_id)
            return
        with tempfile.TemporaryDirectory(prefix='blue-card-') as tmp:
            responses = output / 'responses'
            responses.mkdir(exist_ok=True)
            response = (responses / (blue_id + '.json')).resolve()
            prompt = (output / 'requests' / (blue_id + '.txt')).read_text()
            result = subprocess.run([
                'codex', 'exec', '--skip-git-repo-check', '--ephemeral', '--sandbox', 'read-only',
                '--model', plan['generator']['model'], '-c', 'model_reasoning_effort="' + plan['generator']['effort'] + '"',
                '--output-schema', str(ASSETS / 'output.schema.json'), '-o', str(response), '-'],
                input=prompt, text=True, capture_output=True, cwd=tmp, timeout=600)
            if result.returncode != 0:
                (responses / (blue_id + '.log')).write_text(result.stderr or result.stdout or '')
            require(result.returncode == 0, 'Codex generation failed: ' + blue_id)
            accept(read_json(output / 'requests' / (blue_id + '.json'), 1_000_000), read_json(response), destination)
    failures = []
    with ThreadPoolExecutor(max_workers=jobs) as workers:
        futures = {workers.submit(one, blue_id): blue_id for blue_id in plan['generate']}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as error:
                failures.append(dict(blueId=futures[future], error=str(error)))
    plan['failures'] = failures
    (output / 'result.json').write_bytes(wire(plan))
    require(not failures, 'Some cards failed; successful cards were retained. See ' + str(output / 'result.json'))
    return plan


def summary(report):
    lines = ['## Semantic cards', '',
             f"Required: {len(report['subjects'])}; ready: {len(report['ready'])}; missing: {len(report['missing'])}.",
             '', 'Missing cards do not block package publication. Generation never changes package identities.', '']
    for collection in sorted({c for s in report['subjects'] for c in s.get('collections', [])}):
        selected = {s['blueId'] for s in report['subjects'] if collection in s.get('collections', [])}
        missing = selected.intersection(report['missing'])
        lines.append(f'- {collection}: required {len(selected)}; missing {len(missing)}.')
    lines.append('')
    for item in report['subjects']:
        if item['blueId'] in report['missing']:
            lines.append('- Missing `' + item['alias'].replace('`', '') + '` — `' + item['blueId'] + '`')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('check', 'plan', 'generate', 'accept', 'publish'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, default=Path('build/semantics'))
    parser.add_argument('--bucket')
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--request', type=Path)
    parser.add_argument('--response', type=Path)
    parser.add_argument('--refresh', action='append', default=[], metavar='BLUE_ID',
                        help='Generate selected existing cards into --output/cards for review; repeat per exact ID')
    parser.add_argument('--promote', action='store_true', help='Allow explicitly approved corrections to replace existing S3 cards')
    args = parser.parse_args()
    require(1 <= args.jobs <= 16, '--jobs must be between 1 and 16')
    require(not args.refresh or args.command in {'plan', 'generate'}, '--refresh requires plan or generate')
    root = args.root.resolve()
    if args.command == 'accept':
        require(args.request is not None and args.response is not None, 'accept requires --request and --response')
        card = accept(read_json(args.request, 1_000_000), read_json(args.response), args.output)
        print(card['blueId'])
        return
    store = Store(args.bucket) if args.bucket else None
    if args.command == 'generate':
        result = generate(root, args.output, args.jobs, store, args.refresh)
    elif args.command == 'publish':
        require(store is not None, 'publish requires --bucket')
        subjects, _ = inventory(root)
        cards = cards_in(root)
        keys = store.keys()
        result = {'published': {}, 'missing': sorted(subjects.keys() - cards.keys())}
        for blue_id, card in cards.items():
            result['published'][blue_id] = store.publish(blue_id, card, keys, promote=args.promote)
    elif args.command == 'check':
        subjects, _ = inventory(root)
        cards = cards_in(root)
        result = dict(subjects=list(subjects.values()), ready=sorted(subjects.keys() & cards.keys()),
                      missing=sorted(subjects.keys() - cards.keys()))
    else:
        result = prepare(root, args.output, store, args.refresh)
    if args.command in {'check', 'plan'}:
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as stream:
                stream.write(summary(result))
        if args.command == 'plan' and os.environ.get('GITHUB_OUTPUT'):
            with open(os.environ['GITHUB_OUTPUT'], 'a') as stream:
                stream.write('matrix=' + json.dumps(result['generate']) + '\n')
                stream.write('count=' + str(len(result['generate'])) + '\n')
                for key in ('model', 'effort', 'codexVersion'):
                    stream.write(key + '=' + result['generator'][key] + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
