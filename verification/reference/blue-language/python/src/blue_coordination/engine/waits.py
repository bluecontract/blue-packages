"""Validated, bounded scheduling evidence; never an executable prepared Run."""
from blue_coordination_spec.model import require

FORMAT = 'coordination.preparation-wait/1'


def validate(row, instance):
    require(type(row) is dict and set(row)=={'format','source','facts'} and
        row['format']==FORMAT and type(row['source']) is str and row['source'],
        'INVALID_PREPARATION_WAIT')
    facts=row['facts']
    require(type(facts) is dict and set(facts)=={'points','ranges'} and
        type(facts['points']) is list and type(facts['ranges']) is list,
        'INVALID_PREPARATION_WAIT')
    keys=set()
    for point in facts['points']:
        require(type(point) is list and len(point)==3 and
            all(type(s) is str for s in point[:2]) and
            type(point[2]) is int and point[2]>=0, 'INVALID_PREPARATION_WAIT')
        key=tuple(point[:2]);require(key not in keys,'INVALID_PREPARATION_WAIT');keys.add(key)
    require({('heads',instance),('heads',row['source'])} <= keys,'INVALID_PREPARATION_WAIT')
    count=len(keys);ranges=set()
    for item in facts['ranges']:
        require(type(item) is list and len(item)==3 and
            all(type(s) is str for s in item[:2]) and type(item[2]) is list,
            'INVALID_PREPARATION_WAIT')
        key=tuple(item[:2]);require(key not in ranges,'INVALID_PREPARATION_WAIT');ranges.add(key)
        count+=len(item[2]);previous=None
        for point in item[2]:
            require(type(point) is list and len(point)==2 and type(point[0]) is str and
                point[0].startswith(item[1]) and type(point[1]) is int and point[1]>=0 and
                (previous is None or previous<point[0]),'INVALID_PREPARATION_WAIT')
            previous=point[0]
    require(count<=2048,'INVALID_PREPARATION_WAIT')
    return row
