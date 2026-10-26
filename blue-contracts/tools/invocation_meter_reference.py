"""Independent tariff/cap accounting for actual invocation charge observations.

Logical event selection is checked by paired role/handler vectors, not certified
by receiving a trace here. The unchanged pinned tariff is reused, not the legacy
processor or its old shared-limit default.
"""
import bootstrap
from blue_bex.gas import DEFAULT as BEX_TARIFF
from blue_contracts.reference.model import GAS_PROFILE, TARIFF, integer, require


def check_meter(observation, policy, runtime_tariffs=None):
    require(policy['profile'] == GAS_PROFILE['profile'], 'INCOMPATIBLE_GAS_PROFILE')
    schedules = {'contracts': TARIFF, 'bex': BEX_TARIFF, **(runtime_tariffs or {})}
    shared = integer(policy['shared'])
    local = {key: integer(value, 0, shared) for key, value in policy['local'].items()}
    used, members = 0, {}
    rows = observation['gasTrace']
    for ordinal, row in enumerate(rows):
        require(row['ordinal'] == ordinal, 'INVALID_CHARGE_ORDINAL')
        schedule = schedules.get(row['namespace'])
        require(schedule is not None and row['counter'] in schedule, 'UNSUPPORTED_TARIFF')
        amount = integer(row['units']) * schedule[row['counter']]
        require(row['amount'] == amount, 'INVALID_CHARGE_AMOUNT')
        owner = row['owner']
        require(amount <= shared - used, 'ACCEPTED_CHARGE_EXCEEDS_SHARED_CAP')
        if owner in local:
            require(amount <= local[owner] - members.get(owner, 0), 'ACCEPTED_CHARGE_EXCEEDS_LOCAL_CAP')
        used += amount
        if owner:
            members[owner] = members.get(owner, 0) + amount
    require(observation['gas'] == used, 'INVALID_INVOCATION_GAS')
    rejected = observation.get('rejected')
    if rejected is not None:
        schedule = schedules.get(rejected['namespace'])
        require(schedule is not None and rejected['counter'] in schedule, 'UNSUPPORTED_TARIFF')
        amount = integer(rejected['units']) * schedule[rejected['counter']]
        owner = rejected['owner']
        shared_left = shared - used
        local_left = local[owner] - members.get(owner, 0) if owner in local else None
        require(amount > shared_left or local_left is not None and amount > local_left,
                'REJECTED_CHARGE_WITHIN_CAP')
        local_first = local_left is not None and local_left < shared_left
        expected = {'ordinal': len(rows), 'amount': amount, 'remaining': local_left if local_first else shared_left,
                    'cap': 'LOCAL' if local_first else 'SHARED', 'sharedRemaining': shared_left,
                    'localRemaining': local_left}
        require(all(rejected.get(key) == value for key, value in expected.items()), 'INVALID_REJECTED_CHARGE')
    return {'gas': used, 'memberGas': members, 'qualification': 'TARIFF_AND_CAP_ACCOUNTING_ONLY'}


if __name__ == '__main__':
    import json
    import sys
    from pathlib import Path
    data = json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps({row['label']: check_meter(row['observations'], row['policy'])
                      for row in data['cases']}, indent=2))
