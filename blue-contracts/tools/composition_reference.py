"""Independent composition checks over native contextual observations.

Native identity, Recipe evaluation and authentication remain inputs, not claims
issued by this module. Channel signature encoding is unchanged across editions;
reuse its pinned reference primitive without invoking the legacy processor.
"""
import bootstrap  # Verify pinned native/reference sources before importing primitives.
from copy import deepcopy
from blue_contracts.reference.channels import signature
from blue_contracts.reference.registry import EXTERNAL
from blue_contracts.reference.model import integer, require


def channel_lifetimes(declarations, previous, serials):
    """Derive the next live channel set and generations from actual declarations.

Removed channels retain their monotonic serial. BODY-only declarations cannot
change a lifetime; composite acceptance includes all selected leaf signatures.
"""
    headers = {key: signature(declarations, key) for key, declaration in declarations.items()
               if declaration['_role'] in EXTERNAL}
    next_serials = deepcopy(serials)
    channels = {}
    for key, header in headers.items():
        old = previous.get(key)
        if old is not None and old['signature'] == header:
            require(old['generation'] == next_serials.get(key), 'INVALID_CHANNEL_LIFETIME')
            channels[key] = deepcopy(old)
        else:
            generation = integer(next_serials.get(key, 0) + 1, 1)
            next_serials[key] = generation
            channels[key] = {'generation': generation, 'signature': header}
    return {'channels': channels, 'serials': next_serials}


def check_channel_lifetimes(declarations, channels, serials):
    expected = {key: signature(declarations, key) for key, declaration in declarations.items()
                if declaration['_role'] in EXTERNAL}
    require(set(expected) == set(channels), 'INVALID_CHANNEL_LIFETIMES')
    for key, header in expected.items():
        life = channels[key]
        integer(life['generation'], 1)
        require(life['signature'] == header and life['generation'] == serials.get(key),
                'INVALID_CHANNEL_LIFETIME')
    return {'channels': deepcopy(channels), 'serials': deepcopy(serials)}


def check_channel_trace(observations):
    """Compare independently derived transitions with unmodified native metadata."""
    previous, serials = {}, {}
    checked = []
    for row in observations['transitions']:
        expected = channel_lifetimes(row['declarations'], previous, serials)
        document = row['document']
        actual = {'channels': document['channels'], 'serials': document['channelSerials']}
        require(actual == expected, 'CHANNEL_TRANSITION_MISMATCH', stage=row['label'])
        check_channel_lifetimes(row['declarations'], actual['channels'], actual['serials'])
        previous, serials = expected['channels'], expected['serials']
        checked.append(row['label'])
    return {'checkedTransitions': checked, 'qualification': 'CHANNEL_LIFETIME_TRANSITIONS_ONLY'}


if __name__ == '__main__':
    import json
    import sys
    from pathlib import Path
    print(json.dumps(check_channel_trace(json.loads(Path(sys.argv[1]).read_text())), indent=2))
