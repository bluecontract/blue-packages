"""RCP-1 draft.2 closed internal envelopes. These are NOT BlueIds.

Constructors validate syntax/closure, not authenticity of admissions or
Contracts transitions. Callers must independently establish those facts.
"""
from __future__ import annotations
import hashlib, json, re, unicodedata
from typing import Any, Iterable
from algorithms import blue as L
from .errors import Code, require, CoordinationError

MAX_SAFE_INTEGER = 9007199254740991
SHA = re.compile(r'sha256:[0-9a-f]{64}\Z')
UNSIGNED = re.compile(r'(0|[1-9][0-9]*)\Z')

def closed(value: Any, keys: Iterable[str]) -> dict:
    require(type(value) is dict and set(value) == set(keys), Code.INVALID_EVIDENCE,
            'closed envelope fields differ')
    return value

def scalar_string(value: Any) -> str:
    require(type(value) is str and not any(0xD800 <= ord(c) <= 0xDFFF for c in value),
            Code.INVALID_EVIDENCE, 'expected Unicode scalar string')
    return value

def sha(value: Any) -> str:
    require(type(value) is str and SHA.fullmatch(value) is not None,
            Code.INVALID_EVIDENCE, 'expected lowercase SHA identity')
    return value

def blue_id(value: Any) -> str:
    try:
        scalar_string(value)
        L.final_id(value)
    except L.Failure as error:
        raise CoordinationError(Code.INVALID_EVIDENCE, f'invalid BlueId: {value}') from error
    return value

def document_id(value: Any) -> str:
    value = scalar_string(value)
    require(bool(value) and '\0' not in value and unicodedata.normalize('NFC', value) == value,
            Code.INVALID_EVIDENCE, 'DocumentId must be nonempty NFC without NUL')
    # The underlying Contracts profile supplies any UTF-8 length ceiling.
    # This publication does not invent the missing dependency's numeric limit.
    return value

def unsigned(value: Any, *, safe: bool = False) -> str:
    require(type(value) is str and UNSIGNED.fullmatch(value) is not None,
            Code.INVALID_EVIDENCE, 'noncanonical unsigned decimal')
    require(not safe or int(value) <= MAX_SAFE_INTEGER, Code.INVALID_EVIDENCE, 'unsafe integer')
    return value

def validate_subset(value: Any) -> None:
    if type(value) is str:
        scalar_string(value)
    elif type(value) is list:
        for item in value:
            validate_subset(item)
    elif type(value) is dict:
        for key, item in value.items():
            require(type(key) is str and key.isascii(), Code.INVALID_EVIDENCE, 'non-ASCII envelope key')
            validate_subset(item)
    else:
        require(False, Code.INVALID_EVIDENCE, 'envelopes allow only objects, lists and strings')

def canonical_bytes(value: Any) -> bytes:
    validate_subset(value)
    # For this closed subset ASCII keys give JCS key order; JSON string
    # escaping and Unicode scalar encoding give its remaining encoding.
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def H(domain: str, value: dict) -> str:
    payload = {'domain': scalar_string(domain), 'value': value}
    return 'sha256:' + hashlib.sha256(canonical_bytes(payload)).hexdigest()

def order_record(value: dict) -> dict:
    closed(value, ('timestampUs', 'timelineBlueId', 'entryBlueId'))
    unsigned(value['timestampUs'], safe=True)
    blue_id(value['timelineBlueId']); blue_id(value['entryBlueId'])
    return value

def history_basis(value: dict) -> str:
    closed(value, ('documentId', 'initialDocumentBlueId', 'runtimeSemanticsIdentity', 'admission'))
    document_id(value['documentId']); blue_id(value['initialDocumentBlueId'])
    sha(value['runtimeSemanticsIdentity'])
    a = value['admission']
    require(type(a) is dict, Code.INVALID_EVIDENCE, 'admission object')
    mode = a.get('mode')
    if mode == 'FULL_HISTORY':
        closed(a, ('mode',))
    elif mode in ('FROM_NOW', 'FROM_FRONTIER'):
        closed(a, ('mode', 'lowerExclusiveOrder'))
        bound = a['lowerExclusiveOrder']
        if mode == 'FROM_NOW' and bound == {'kind': 'BEGINNING'}:
            pass  # Authenticated beginning is a separate admission prerequisite.
        else:
            order_record(bound)
    elif mode == 'CREATED_IN_OPERATION':
        closed(a, ('mode', 'creatorOperationIdentity', 'birthOccurrenceIdentity', 'lowerExclusiveOrder'))
        sha(a['creatorOperationIdentity']); sha(a['birthOccurrenceIdentity'])
        order_record(a['lowerExclusiveOrder'])
    else:
        require(False, Code.INVALID_EVIDENCE, 'unknown admission mode')
    return H('blue-document-history-basis/1.0-draft.2', value)

def unique_sorted(rows: list[dict], key) -> list[dict]:
    ordered = sorted(rows, key=key)
    keys = [key(row) for row in ordered]
    require(len(set(keys)) == len(keys), Code.INVALID_EVIDENCE, 'duplicate set member')
    return ordered

def operation_owner(members: list[dict], internal_edges: list[dict]) -> tuple[str, str, dict]:
    require(bool(members), Code.INVALID_EVIDENCE, 'empty owner set')
    for row in members:
        closed(row, ('documentId', 'historyBasisIdentity'))
        document_id(row['documentId']); sha(row['historyBasisIdentity'])
    members = unique_sorted(members, lambda r: r['documentId'].encode('utf-8'))
    ids = {m['documentId'] for m in members}
    for e in internal_edges:
        closed(e, ('occurrenceIdentity', 'parentDocumentId', 'sourcePath', 'childDocumentId', 'activationGeneration'))
        sha(e['occurrenceIdentity']); unsigned(e['activationGeneration'])
        document_id(e['parentDocumentId']); document_id(e['childDocumentId'])
        scalar_string(e['sourcePath'])
        require(e['sourcePath'].startswith('/'), Code.INVALID_EVIDENCE, 'source path must be an exact pointer')
        L.path_parts(e['sourcePath'])
        require(e['parentDocumentId'] in ids and e['childDocumentId'] in ids,
                Code.INVALID_EVIDENCE, 'owner edge endpoint outside owner set')
    edges = unique_sorted(internal_edges, lambda e: e['occurrenceIdentity'].encode('utf-8'))
    value = {'members': members, 'internalEdges': edges}
    return members[0]['documentId'], H('blue-operation-owner/1.0-draft.2', value), value

def root_context(canonical_root: str, owner_identity: str) -> str:
    document_id(canonical_root); sha(owner_identity)
    return H('blue-contracts-root-processing-context/1.0-draft.2', {
        'canonicalRootDocumentId': canonical_root, 'operationOwnerIdentity': owner_identity})

def delivery_basis(value: dict) -> str:
    closed(value, ('operationOwnerIdentity', 'causeIdentity', 'kind', 'receivingBindings', 'sourcePositionIdentity'))
    sha(value['operationOwnerIdentity']); sha(value['causeIdentity'])
    kind = value['kind']
    require(kind in ('ADMISSION', 'LIVE', 'MANAGED_REVISION', 'MANAGED_REPRESENTATION'),
            Code.INVALID_EVIDENCE, 'unsupported cause kind')
    rows = value['receivingBindings']
    require(type(rows) is list, Code.INVALID_EVIDENCE, 'receivingBindings array')
    for r in rows:
        closed(r, ('documentId', 'scopePath', 'activationGeneration', 'channelKey', 'occurrenceIdentity'))
        document_id(r['documentId']); scalar_string(r['scopePath']); L.path_parts(r['scopePath'])
        unsigned(r['activationGeneration']); scalar_string(r['channelKey']); sha(r['occurrenceIdentity'])
    position = value['sourcePositionIdentity']
    if kind in ('ADMISSION', 'LIVE'):
        require(position == {'kind': 'NONE'}, Code.INVALID_EVIDENCE, 'non-retained position must be NONE')
    else:
        closed(position, ('kind', 'identity'))
        require(position['kind'] == 'POSITION', Code.INVALID_EVIDENCE, 'retained position tag')
        sha(position['identity'])
    normalized = dict(value, receivingBindings=unique_sorted(rows, canonical_bytes))
    return H('blue-rooted-delivery-basis/1.0-draft.2', normalized)

def rooted_invocation(base: str, context: str, delivery: str) -> str:
    return H('blue-contracts-rooted-invocation/1.0-draft.2', {
        'baseInvocationIdentity': sha(base), 'rootProcessingContextIdentity': sha(context),
        'deliveryBasisIdentity': sha(delivery)})

def rooted_companion(base: str, invocation: str, context: str) -> str:
    return H('blue-contracts-rooted-commit-companion/1.0-draft.2', {
        'baseCommitCompanionIdentity': sha(base), 'rootedInvocationIdentity': sha(invocation),
        'rootProcessingContextIdentity': sha(context)})

def terminal_key(owner: str, delivery: str) -> str:
    return H('blue-coordination-rooted-terminal-key/1.0-draft.2', {
        'operationOwnerIdentity': sha(owner), 'deliveryBasisIdentity': sha(delivery)})
