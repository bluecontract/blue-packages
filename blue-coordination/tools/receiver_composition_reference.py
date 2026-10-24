"""Independent receiver decisions over native authenticated journal observations.

No serialized field here grants authority. The Java adapter must first admit the
signed source, mint PRE from the journal and compare after reopening SQLite.
"""
from receiver_reference import Before, classify_operation, replay_frontier


def derive_decisions(observation):
    raw = observation['pre']
    before = Before(raw['current'], frozenset(raw['ownPast']), frozenset(raw['foreign']), raw['complete'])
    choices = [classify_operation(row['target'], row['exact'], before)
               for row in observation['selections']]
    order = tuple(observation['bound'])
    entries = tuple(tuple(row) for row in observation['orderedEntries'])
    return {'selections': choices,
            **{phase: [list(key) for key in replay_frontier(phase, order, entries)]
               for phase in ('INITIAL', 'ACTIVATION')}}


def check_observations(observation):
    expected = derive_decisions(observation)
    actual = {'selections': [row['actual'] for row in observation['selections']],
              'INITIAL': observation['INITIAL'], 'ACTIVATION': observation['ACTIVATION']}
    if actual != expected:
        raise ValueError('NATIVE_RECEIVER_COMPOSITION_MISMATCH')
    return expected


if __name__ == '__main__':
    import json
    import sys
    from pathlib import Path
    print(json.dumps(check_observations(json.loads(Path(sys.argv[1]).read_text())), indent=2))
