"""Discover semantic subjects from checked package records, without executing Blue."""
import json
import re
import zipfile
import io

import yaml

from release import check_archive, digest, local, require, selections, wire

BLUE_ID = re.compile(r'[1-9A-HJ-NP-Za-km-z]{32,64}')
PRIMITIVES = {
    'GX7CFUmSDrE2MzptunLCCdZwnuwwrenRQqEnHL4x3uoC': str,
    'AwvXD961fmnmqcSQhjMA7r15HpVh39cefb6ZTyUz2Fm2': bool,
    'E2LM6qgzWG9ttagq2xTmiZkgYEAgkYedFCmU9v7NnVEq': int,
}
STRUCTURAL = {'type', 'name', 'description', 'blueId', 'contracts', 'clauses',
              'functions', 'actions', 'bindingTypes', 'defaultBindings', 'bindings',
              'parameters', 'actionDefinition', 'hookDefinition', 'hookAbi', 'specification'}


def references(value):
    if isinstance(value, list):
        return set().union(*(references(v) for v in value))
    if not isinstance(value, dict):
        return set()
    found = {value['blueId']} if isinstance(value.get('blueId'), str) else set()
    return found | set().union(*(references(v) for k, v in value.items() if k != 'blueId'))


def compact(value):
    if isinstance(value, list):
        return [compact(v) for v in value]
    if not isinstance(value, dict):
        return value
    expected = PRIMITIVES.get(value.get('type', {}).get('blueId')) if isinstance(value.get('type'), dict) else None
    if set(value) == {'type', 'value'} and expected and type(value['value']) is expected:
        return value['value']
    return {k: compact(v) for k, v in value.items()}


def type_chain(blue_id, definitions):
    seen = set()
    while blue_id in definitions:
        require(blue_id not in seen, 'Type inheritance cycle: ' + blue_id)
        seen.add(blue_id)
        value = definitions[blue_id]
        if not isinstance(value, dict):
            break
        yield blue_id, value
        blue_id = value.get('type', {}).get('blueId') if isinstance(value.get('type'), dict) else None


def discover(exports, definitions, clause_id):
    """All exported Clause descendants and clause hosts; names are not classifiers."""
    selected = {}
    for blue_id, exported in exports.items():
        chain = list(type_chain(blue_id, definitions))
        roles = []
        if any(identity == clause_id for identity, _ in chain):
            roles.append('clause')
        if any('clauses' in value for _, value in chain):
            roles.append('host')
        if roles:
            selected[blue_id] = dict(exported, roles=roles)
    # Hosts, nested clauses, child templates and explicit executable definitions
    # can need cards even when their exported type is not itself a Clause.
    pending = list(selected)
    while pending:
        blue_id = pending.pop()
        for identity, value in type_chain(blue_id, definitions):
            if selected[blue_id]['roles'] == ['helper'] and identity in exports and identity not in selected:
                selected[identity] = dict(exports[identity], roles=['helper'])
            def visit(node):
                if isinstance(node, list):
                    for child in node:
                        visit(child)
                elif isinstance(node, dict):
                    for key, child in node.items():
                        if key.lower().endswith('definition') or key.lower().endswith('template') or key == 'instructionClauses':
                            for ref in references(child):
                                if ref in exports and ref not in selected:
                                    selected[ref] = dict(exports[ref], roles=['helper'])
                                    pending.append(ref)
                        visit(child)
            visit(value)
    return dict(sorted(selected.items()))


def source_collections(root):
    """Current publications plus explicitly pinned, dependency-closed collections."""
    yield 'current', selections(root), False
    path = local(root, 'semantics/collections.json')
    if not path.exists():
        return
    config = json.loads(path.read_bytes())
    require(config['format'] == 'blue-semantic-collections/1', 'Unknown semantic collection format')
    names = {'current'}
    for collection in config['collections']:
        name = collection['name']
        require(name not in names, 'Duplicate semantic collection: ' + name)
        names.add(name)
        pin = collection['selection']
        data = local(root, pin['path']).read_bytes()
        require(digest(data) == pin['sha256'], 'Semantic selection checksum differs: ' + name)
        defaults = json.loads(data)
        require(defaults['format'] == 'myos-default-packages/1', 'Unknown default package format')
        packages = {p['blueId']: p for p in collection['packages']}
        require(len(packages) == len(collection['packages']), 'Duplicate semantic package identity')
        roots = defaults['packages']
        require(roots and len({p['name'] for p in roots}) == len(roots)
                and len({p['blueId'] for p in roots}) == len(roots), 'Invalid semantic selection')
        for selected in roots:
            package = packages.get(selected['blueId'], {})
            require(all(package.get(k) == selected[k] for k in ('id', 'name', 'blueId')),
                    'Semantic selection differs from pinned package: ' + selected['name'])
        pending, included = [p['blueId'] for p in roots], set()
        while pending:
            blue_id = pending.pop()
            if blue_id in included:
                continue
            require(blue_id in packages, 'Missing semantic dependency: ' + blue_id)
            included.add(blue_id)
            pending.extend(packages[blue_id]['imports'].values())
        require(included == packages.keys(), 'Unselected packages in semantic collection: ' + name)
        yield name, [dict(p, packageBlueId=p['blueId']) for p in packages.values()], True


def collection_inventory(root, rows, *, retained=False):
    definitions, exports, aliases = {}, {}, {}
    for row in rows:
        checked, data = check_archive(root, row, retained=retained)
        if retained:
            require(row['id'] == checked['name'] + '@' + checked['version'] + '+' + row['packageBlueId']
                    and row['version'] == checked['version'] and row['imports'] == checked['imports']
                    and row['exports'] == {e['name']: e['blueId'] for e in checked['exports']}
                    and all(e['alias'] == row['name'] + '/' + e['name'] for e in checked['exports']),
                    'Semantic catalogue differs from archive: ' + row['name'])
        else:
            config = yaml.safe_load(local(root, row['directory'] + '/blue-package.yaml').read_text())
            authored = {e['name'] for e in config['exports']}
            built = {e['name'] for e in checked['exports']}
            require(authored == built, 'Unbuilt exports in ' + row['name'] + '; rebuild the package')
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            records = json.loads(archive.read('package-records.json'))
        for blue_id, record in records.items():
            if record.get('mode') != 'exact':
                continue
            definition = json.loads(record['text'])
            if blue_id in definitions:
                require(definitions[blue_id] == definition, 'Conflicting exact definition: ' + blue_id)
            else:
                definitions[blue_id] = definition
        for entry in checked['exports']:
            blue_id = entry['blueId']
            require(BLUE_ID.fullmatch(blue_id) is not None, 'Invalid exported BlueId')
            require(blue_id in definitions, 'Missing exact export: ' + entry['alias'])
            require(entry['alias'] not in aliases or aliases[entry['alias']] == blue_id,
                    'Conflicting export alias in collection: ' + entry['alias'])
            aliases[entry['alias']] = blue_id
            exports.setdefault(blue_id, dict(blueId=blue_id, alias=entry['alias'], package={
                'name': row['name'], 'version': checked['version'],
                'blueId': row['packageBlueId'], 'archiveSha256': row['archiveSha256']}))
    require('Clauses/Clause' in aliases, 'The selected collection has no Clauses/Clause base')
    return discover(exports, definitions, aliases['Clauses/Clause']), definitions


def inventory(root):
    subjects, definitions = {}, {}
    for name, rows, retained in source_collections(root):
        selected, exact = collection_inventory(root, rows, retained=retained)
        for blue_id, definition in exact.items():
            require(blue_id not in definitions or definitions[blue_id] == definition,
                    'Conflicting exact definition across collections: ' + blue_id)
            definitions[blue_id] = definition
        for blue_id, subject in selected.items():
            subjects.setdefault(blue_id, dict(subject, collections=[]))['collections'].append(name)
    return dict(sorted(subjects.items())), definitions


def pointer(value):
    return isinstance(value, str) and value.startswith('/') and len(value) <= 256 and not re.search(r'\s|~(?![01])', value)


def evidence(blue_id, definitions):
    root = compact(definitions[blue_id])
    require(len(wire(root)) <= 200_000, 'Root definition exceeds semantic context budget: ' + blue_id)
    supplied, omitted, visited = {}, set(), {blue_id}
    # Include inheritance first, so optional event/helper references cannot crowd it out.
    queue = [(identity, 0) for identity, _ in list(type_chain(blue_id, definitions))[1:]]
    queue += [(ref, 1) for ref in sorted(references(root))]
    size = 0
    while queue:
        ref, depth = queue.pop(0)
        if ref in visited or ref in PRIMITIVES:
            continue
        visited.add(ref)
        value = compact(definitions[ref]) if ref in definitions else None
        length = len(wire(value)) if value is not None else 0
        if value is None or depth > 3 or len(supplied) >= 128 or size + length > 240_000:
            omitted.add(ref)
            continue
        supplied[ref] = value
        size += length
        queue.extend((child, depth + 1) for child in sorted(references(value)))
    bindings, parameters, paths = {}, set(), set()

    def fields(node, path, depth=0):
        if depth > 32 or not pointer(path):
            return
        paths.add(path)
        if not isinstance(node, dict):
            return
        if '$object' in node:
            node = node['$object']
        elif isinstance(node.get('$merge'), list):
            for part in node['$merge']:
                fields(part, path, depth + 1)
            return
        if not isinstance(node, dict) or any(k.startswith('$') for k in node):
            return
        for key, child in node.items():
            if key not in {'type', 'blueId'}:
                fields(child, path + '/' + key.replace('~', '~0').replace('/', '~1'), depth + 1)

    for _, raw in type_chain(blue_id, definitions):
        node = compact(raw)
        for name in node.get('bindingTypes', {}):
            bindings.setdefault(name, None)
        for name, default in node.get('defaultBindings', {}).items():
            bindings.setdefault(name, None)
            if bindings[name] is None and isinstance(default, str):
                bindings[name] = default
        parameters.update('parameters.' + name for name in node.get('parameters', {}))
        for key, value in node.items():
            if key not in STRUCTURAL and not key.lower().endswith('template'):
                fields(value, '/' + key.replace('~', '~0').replace('/', '~1'))

    def literals(value):
        if isinstance(value, list):
            for child in value:
                literals(child)
        elif isinstance(value, dict):
            if pointer(value.get('$document')):
                paths.add(value['$document'])
            change = value.get('$appendChange')
            if isinstance(change, dict) and change.get('op') in {'add', 'replace'}:
                fields(change.get('val'), change.get('path'))
            for child in value.values():
                literals(child)

    literals([root, *supplied.values()])
    return dict(blueId=blue_id, definition=root,
                bindings=[dict(name=k, defaultPath=v) for k, v in sorted(bindings.items())],
                parameterRefs=sorted(parameters | {'bindings.' + name for name in bindings}),
                documentPaths=sorted(paths), referencedBlueIds=sorted((visited | omitted) - {blue_id}),
                dependencyDefinitions=[dict(blueId=k, definition=v) for k, v in sorted(supplied.items())],
                omittedDependencies=sorted(omitted))


def definition_digest(blue_id, definitions):
    return digest(wire(definitions[blue_id]))
