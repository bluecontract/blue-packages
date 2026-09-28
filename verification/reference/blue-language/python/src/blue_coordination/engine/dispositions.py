"""Private, durable feeder decisions; never successful Contracts checkpoints."""
from .store import fingerprint
from blue_coordination_spec.model import require

FORMAT = 'coordination.input-disposition/1'
REJECTIONS = frozenset({'INVALID_TARGET_OPERATION', 'INVALID_TARGET_CHANNEL',
    'INVALID_REQUEST', 'STALE_DOCUMENT_PRECONDITION', 'BEX_EXECUTION_REJECTED',
    'GAS_LIMIT_EXCEEDED'})


def key(instance, member, channel, generation, entry):
    return fingerprint([instance, member, channel, generation, entry])


def validate(row):
    require(type(row) is dict and set(row) == {'format', 'instance', 'lineage',
        'entry', 'order', 'before', 'scope', 'evidence', 'outcome', 'reason', 'result'},
        'INVALID_INPUT_DISPOSITION')
    require(row['format'] == FORMAT and row['outcome'] in
        ('REJECTED', 'EXECUTION_REJECTED', 'NO_MATCH'), 'INVALID_INPUT_DISPOSITION')
    require(type(row['order']) is list and len(row['order']) == 3 and
        type(row['order'][0]) is int and row['order'][0] >= 0 and
        type(row['order'][1]) is str and bool(row['order'][1]) and
        row['order'][2] == row['entry'], 'INVALID_INPUT_DISPOSITION')
    require(all(type(row[k]) is str and row[k] for k in
        ('instance', 'lineage', 'entry', 'before', 'reason')), 'INVALID_INPUT_DISPOSITION')
    require(type(row['scope']) is list and row['scope'], 'INVALID_INPUT_DISPOSITION')
    for s in row['scope']:
        require(type(s) is dict and set(s) == {'member','channel','generation'} and
            type(s['generation']) is int and s['generation'] >= 0 and
            all(type(s[k]) is str and s[k] for k in ('member','channel')), 'INVALID_INPUT_DISPOSITION')
    require(len({(s['member'],s['channel'],s['generation']) for s in row['scope']}) == len(row['scope']),
        'INVALID_INPUT_DISPOSITION')
    allowed = {'NO_MATCH': {'NO_MATCH'}, 'REJECTED': (REJECTIONS -
        {'BEX_EXECUTION_REJECTED','GAS_LIMIT_EXCEEDED'}) | {'AUTHORITY_DENIED'},
        'EXECUTION_REJECTED': {'BEX_EXECUTION_REJECTED','GAS_LIMIT_EXCEEDED'}}
    require(row['reason'] in allowed[row['outcome']], 'INVALID_INPUT_DISPOSITION')
    require(type(row['evidence']) is dict and
        (row['result'] is None or type(row['result']) is dict), 'INVALID_INPUT_DISPOSITION')
    return row
