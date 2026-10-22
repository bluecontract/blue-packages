#!/usr/bin/env python3
"""Check, prepare, generate, import or publish exact public semantic cards."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from jsonschema import Draft202012Validator

from release import ROOT, digest, local, require, wire
from semantic_sources import BLUE_ID, definition_digest, evidence, inventory, pointer
from semantic_s3 import MAX_CARD_BYTES, Store, card_key

ASSETS = Path(__file__).resolve().parents[1] / 'semantics'
OUTPUT_SCHEMA = json.loads((ASSETS / 'output.schema.json').read_text())
VALIDATOR = Draft202012Validator(OUTPUT_SCHEMA)
HASH = re.compile(r'sha256:[0-9a-f]{64}')
CARD_KEYS = {'format', 'language', 'blueId', 'semanticText', 'semanticHash', 'metadata',
             'definitionDigest', 'sourceDigest', 'package', 'generator', 'review', 'validation'}


def read_json(path, limit=MAX_CARD_BYTES):
    require(not path.is_symlink(), 'Symlink is not a semantic artifact: ' + str(path))
    require(path.stat().st_size <= limit, 'Semantic artifact exceeds its size limit: ' + str(path))
    return json.loads(path.read_bytes())


def validate_output(value, context=None):
    VALIDATOR.validate(value)
    require(value['semanticText'].lstrip().startswith('# '), 'Card text needs a heading')
    require(len(value['semanticText'].encode()) <= 48_000, 'Card text exceeds the byte limit')
    metadata = value['metadata']
    require(len(wire(metadata)) <= 16_384, 'Card metadata exceeds the byte limit')
    facts = metadata['stateFacts']
    require(len({fact['id'] for fact in facts}) == len(facts), 'Duplicate state fact')
    for fact in facts:
        require(fact['suffix'] == '' or pointer(fact['suffix']), 'Invalid fact suffix')
        require(fact['aggregate'] is None or fact['type'] in {'number', 'count', 'money-minor'}, 'Aggregate must be numeric')
        if fact['scope'] == 'document':
            require(pointer(fact['path']) and fact['binding'] is None and fact['defaultPath'] is None
                    and fact['suffix'] == '', 'Invalid document fact')
        else:
            require(fact['path'] is None and isinstance(fact['binding'], str)
                    and (fact['defaultPath'] is None or pointer(fact['defaultPath'])), 'Invalid binding fact')
    if context is None:
        return
    require(value['blueId'] == context['blueId'], 'Generated BlueId differs from source')
    require(set(metadata['parameterRefs']) <= set(context['parameterRefs']), 'Unestablished parameter reference')
    require(set(metadata['covers'] + metadata['dependencies']) <= set(context['referencedBlueIds']), 'Unestablished dependency')
    bindings = {b['name']: b['defaultPath'] for b in context['bindings']}
    for fact in facts:
        if fact['scope'] == 'document':
            require(fact['path'] in context['documentPaths'], 'Unestablished document fact path')
        else:
            require(fact['binding'] in bindings and bindings[fact['binding']] == fact['defaultPath'], 'Unestablished binding/default')


def validate_card(card, blue_id, definitions=None):
    require(isinstance(card, dict) and set(card) == CARD_KEYS, 'Invalid card envelope')
    require(card['format'] == 'blue-semantic-card/1' and card['language'] == 'en', 'Incompatible semantic card')
    require(BLUE_ID.fullmatch(blue_id) is not None and card['blueId'] == blue_id, 'Card filename/BlueId mismatch')
    require(card['validation'] == {'state': 'valid', 'problems': []}, 'Card has not passed validation')
    for field in ('semanticHash', 'definitionDigest', 'sourceDigest'):
        require(isinstance(card[field], str) and HASH.fullmatch(card[field]), 'Invalid ' + field)
    require(card['semanticHash'] == digest(card['semanticText'].encode()), 'Semantic text hash mismatch')
    package = card['package']
    require(isinstance(package, dict) and set(package) == {'name', 'version', 'blueId', 'archiveSha256'}, 'Invalid package provenance')
    require(all(isinstance(v, str) and 0 < len(v) <= 200 for v in package.values()), 'Invalid package provenance value')
    require(BLUE_ID.fullmatch(package['blueId']) and HASH.fullmatch(package['archiveSha256']), 'Invalid package identity')
    generator = card['generator']
    require(isinstance(generator, dict) and set(generator) == {'model', 'effort', 'codexVersion', 'promptVersion', 'promptSha256'}, 'Invalid generator provenance')
    require(all(isinstance(v, str) and 0 < len(v) <= 200 for v in generator.values()), 'Invalid generator provenance value')
    require(HASH.fullmatch(generator['promptSha256']), 'Invalid prompt hash')
    review = card['review']
    require(isinstance(review, dict) and set(review) == {'state', 'basis'}
            and review['state'] in {'unreviewed', 'static-reviewed', 'corrected'}, 'Unusable review state')
    require(review['basis'] is None or isinstance(review['basis'], str) and len(review['basis']) <= 2000, 'Invalid review basis')
    require(review['state'] == 'unreviewed' or bool(review['basis']), 'Reviewed card needs a review basis')
    context = None
    if definitions is not None and blue_id in definitions:
        require(card['definitionDigest'] == definition_digest(blue_id, definitions), 'Card definition digest mismatch')
        context = evidence(blue_id, definitions)
    validate_output({k: card[k] for k in ('blueId', 'semanticText', 'metadata')}, context)
    require(len(wire(card)) <= MAX_CARD_BYTES, 'Card exceeds stored byte limit')
    return card


def cards_in(root, definitions=None):
    require(not (root / 'semantics').is_symlink() and not (root / 'semantics/cards').is_symlink(),
            'Semantic directories cannot be symlinks')
    folder = local(root, 'semantics/cards')
    cards = {}
    for path in sorted(folder.glob('*.json')):
        cards[path.stem] = validate_card(read_json(path), path.stem, definitions)
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


def prepare(root, output, store=None):
    subjects, definitions = inventory(root)
    cards = cards_in(root, definitions)
    keys = store.keys() if store else set()
    restored = []
    for blue_id in subjects.keys() - cards.keys():
        card = store.restore(blue_id, keys) if store else None
        if card is not None:
            validate_card(card, blue_id, definitions)
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
    output.mkdir(parents=True, exist_ok=True)
    requests = output / 'requests'
    requests.mkdir(exist_ok=True)
    # GitHub matrices allow at most 256 jobs. A committed batch triggers the next
    # coverage run, which discovers the remaining IDs without regenerating these.
    batch = missing[:256]
    for blue_id in batch:
        context = evidence(blue_id, definitions)
        request = dict(context=context, definitionDigest=definition_digest(blue_id, definitions),
                       sourceDigest=digest(wire(context)), package=subjects[blue_id]['package'], generator=generator)
        (requests / (blue_id + '.json')).write_bytes(wire(request))
        (requests / (blue_id + '.txt')).write_text(prompt + '\n\nEvidence (JSON):\n' + wire(context).decode())
    report = dict(format='blue-semantic-plan/1', subjects=list(subjects.values()),
                  ready=sorted(subjects.keys() & cards.keys()), restored=sorted(restored), missing=missing,
                  generate=batch, unpublished=sorted(id for id in cards if store and card_key(id) not in keys),
                  remoteChecked=store is not None, generator=generator)
    (output / 'plan.json').write_bytes(wire(report))
    return report


def accept(request, response, output):
    context = request['context']
    require(request['sourceDigest'] == digest(wire(context)), 'Generation request checksum mismatch')
    validate_output(response, context)
    card = dict(response, format='blue-semantic-card/1', language='en',
                semanticHash=digest(response['semanticText'].encode()),
                definitionDigest=request['definitionDigest'], sourceDigest=request['sourceDigest'],
                package=request['package'], generator=request['generator'],
                validation={'state': 'valid', 'problems': []}, review={'state': 'unreviewed', 'basis': None})
    validate_card(card, context['blueId'])
    save_card(output, card)
    return card


def generate(root, output, jobs, store=None):
    plan = prepare(root, output, store)
    destination = local(root, 'semantics/cards')
    for blue_id in plan['restored']:
        save_card(destination, read_json(output / 'cards' / (blue_id + '.json')))
    if not plan['generate']:
        return plan
    version = subprocess.check_output(['codex', '--version'], text=True).strip()
    require(version == 'codex-cli ' + plan['generator']['codexVersion'], 'Install the pinned Codex CLI version from semantics/generator.json')

    def one(blue_id):
        if (destination / (blue_id + '.json')).exists():
            validate_card(read_json(destination / (blue_id + '.json')), blue_id)
            return
        with tempfile.TemporaryDirectory(prefix='blue-card-') as tmp:
            response = Path(tmp) / 'response.json'
            prompt = (output / 'requests' / (blue_id + '.txt')).read_text()
            result = subprocess.run([
                'codex', 'exec', '--skip-git-repo-check', '--ephemeral', '--sandbox', 'read-only',
                '--model', plan['generator']['model'], '-c', 'model_reasoning_effort="' + plan['generator']['effort'] + '"',
                '--output-schema', str(ASSETS / 'output.schema.json'), '-o', str(response), '-'],
                input=prompt, text=True, capture_output=True, cwd=tmp, timeout=600)
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
    parser.add_argument('--promote', action='store_true', help='Allow explicitly approved corrections to replace existing S3 cards')
    args = parser.parse_args()
    require(1 <= args.jobs <= 16, '--jobs must be between 1 and 16')
    root = args.root.resolve()
    if args.command == 'accept':
        require(args.request is not None and args.response is not None, 'accept requires --request and --response')
        card = accept(read_json(args.request, 1_000_000), read_json(args.response), args.output)
        print(card['blueId'])
        return
    store = Store(args.bucket) if args.bucket else None
    if args.command == 'generate':
        result = generate(root, args.output, args.jobs, store)
    elif args.command == 'publish':
        require(store is not None, 'publish requires --bucket')
        subjects, definitions = inventory(root)
        cards = cards_in(root, definitions)
        keys = store.keys()
        result = {'published': {}, 'missing': sorted(subjects.keys() - cards.keys())}
        for blue_id, card in cards.items():
            result['published'][blue_id] = store.publish(blue_id, card, keys, promote=args.promote)
    elif args.command == 'check':
        subjects, definitions = inventory(root)
        cards = cards_in(root, definitions)
        result = dict(subjects=list(subjects.values()), ready=sorted(subjects.keys() & cards.keys()),
                      missing=sorted(subjects.keys() - cards.keys()))
    else:
        result = prepare(root, args.output, store)
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
