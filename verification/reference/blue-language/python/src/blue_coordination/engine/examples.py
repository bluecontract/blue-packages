"""Executable teaching and load scenarios, shared by UI and benchmarks."""
from copy import deepcopy


def operation(channel, path, value):
    return {'type': 'Contracts/Sequential Workflow Operation', 'channel': channel,
        'steps': [{'type': 'Contracts/Compute', 'do': [{'$appendChange': {
            'op': 'replace', 'path': path, 'val': value}}]}]}


def counter(catalogue, timeline, actor, name='Counter', operations=1):
    document = {'name': name, 'count': 0, 'contracts': {
        'in': catalogue.typed('Timeline Channel', timeline={'blueId': timeline}, actor={'blueId': actor})}}
    for i in range(operations):
        name = 'increment' if i == 0 else 'incrementBy' + str(i + 1)
        document['contracts'][name] = operation('in', '/count', {'$add': [{'$document': '/count'}, i + 1]})
    return document


def agreement(catalogue, timeline, actor, *, orders=8, payments=3, operations=8):
    """Business graph with independent operations and substantial local state.

    Definitions deliberately use ordinary open Blue documents: this benchmark
    isolates Coordination cost from the separately versioned business repository.
    All children have distinct content/lineages and genuine initialization.
    """
    def business(kind, key):
        document = counter(catalogue, timeline, actor, kind + ' ' + key, operations)
        document.update(businessId=key, status='Draft', amount=1000, currency='EUR',
            revision=0, approved=False, tags=['wholesale', 'EU', 'priority'],
            contacts={'buyer': {'name': 'Northwind', 'email': 'buyer@example.test'},
                      'seller': {'name': 'Blue Supply', 'email': 'seller@example.test'}},
            audit={'createdBy': 'demo', 'reference': key, 'notes': []},
            terms={'settlementDays': 30, 'discountBps': 125, 'jurisdiction': 'EU'})
        document['contracts']['approve'] = operation('in', '/approved', True)
        document['contracts']['release'] = operation('in', '/status', 'Released')
        document['contracts']['revise'] = operation('in', '/revision', {'$add': [{'$document': '/revision'}, 1]})
        return document
    root = business('Agreement', 'AGR-2026')
    root['orders'] = {}
    root['contracts']['embedded'] = {'type': 'Contracts/Process Embedded', 'collectionPaths': ['/orders']}
    for i in range(orders):
        order = business('Order', f'ORD-{i:03}')
        order['products'] = {f'SKU-{j:03}': {'quantity': j + 1, 'unitPrice': 35 + j,
            'description': 'Manufactured component ' + str(j), 'specification': {'grade': 'A', 'weightGrams': 150 + j}}
            for j in range(8)}
        order['payments'] = {str(j): business('Payment', f'PAY-{i:03}-{j:03}') for j in range(payments)}
        order['contracts']['embedded'] = {'type': 'Contracts/Process Embedded', 'collectionPaths': ['/payments']}
        root['orders'][str(i)] = order
    return root


LESSONS = [
    dict(id='counter', title='An automatic counter', summary='Initialize, append an authenticated operation, and read its stable epoch.',
        steps=['Start the counter', 'Increment once', 'Increment again', 'Inspect history and gas']),
    dict(id='children', title='Three new independent documents', summary='Create a collection, then address a child without calling the parent.',
        steps=['Start the factory', 'Create three children', 'Increment the first child', 'Inspect every managed document']),
    dict(id='missing', title='Missing content, then recovery', summary='An unknown exact BlueId waits honestly; supplying its content resumes the original registration.',
        steps=['Register an unavailable document', 'Supply the exact content', 'Increment the resumed document', 'Inspect the stable state']),
    dict(id='mandate', title='An approved permission for another actor', summary='Alice approves an exact Mandate; Bob uses its scope and remains the actual actor.',
        steps=['Start Alice’s counter', 'Create the pending Mandate', 'Approve this exact version', 'Let Bob increment', 'Terminate the permission', 'Try Bob’s operation again', 'Inspect authority and history']),
    dict(id='agreement', title='Agreement → orders → payments', summary='A substantial graph with operations at all three levels and measured propagation.',
        steps=['Start 8 orders and 24 payments', 'Approve the agreement', 'Revise the first order', 'Release its first payment', 'Inspect timings and history']),
    dict(id='rejected-input', title='A rejected request does not stop the counter',
        summary='A missing operation gets a durable rejection. It adds no epoch or checkpoint, and the next valid request still runs.',
        steps=['Start the counter', 'Increment once', 'Submit a nonexistent operation', 'Increment after the rejection', 'Compare the two epochs with three inputs']),
    dict(id='ordinary-observer', title='An observer on a different channel',
        summary='The Child receives an addressed operation on owner. The Root observes the same original entry on rootChannel and reads the completed Child.',
        steps=['Start the Root and Child', 'Address increment to the Child', 'Inspect Root.seen and Child.count']),
]


def ordinary_observer(catalogue, timeline, actor):
    channel = catalogue.typed('Timeline Channel', timeline={'blueId':timeline}, actor={'blueId':actor})
    child = {'name':'Observed Child','count':0,'contracts':{'owner':channel,
        'increment':operation('owner','/count',{'$add':[{'$document':'/count'},1]})}}
    return {'name':'Observing Root','seen':0,'child':child,'contracts':{
        'rootChannel':channel,
        'embedded':{'type':'Contracts/Process Embedded','paths':['/child']},
        'observe':{'type':'Contracts/Sequential Workflow','channel':'rootChannel',
            'steps':operation('rootChannel','/seen',{'$document':'/child/count'})['steps']}}}


def mandate(catalogue, lineage, owner_timeline, owner_actor, delegate_timeline, delegate_actor):
    return catalogue.typed('Mandate/Operation Mandate', name='Counter permission', contracts={
        'authorityHolderChannel': catalogue.typed('Timeline Channel', timeline={'blueId': owner_timeline}, actor={'blueId': owner_actor}),
        'authorizedActorChannel': catalogue.typed('Timeline Channel', timeline={'blueId': delegate_timeline}, actor={'blueId': delegate_actor})},
        scope={'increment': catalogue.typed('Mandate/Operation Grant', target={
            'initialDocument': {'blueId': lineage}, 'channel': 'in', 'operation': 'increment'})})


def factory(catalogue, timeline, actor):
    root = counter(catalogue, timeline, actor, 'Factory')
    root['children'] = {}
    children = {str(i): counter(catalogue, timeline, actor, 'Child ' + str(i)) for i in range(3)}
    root['contracts']['embedded'] = {'type': 'Contracts/Process Embedded', 'collectionPaths': ['/children']}
    root['contracts']['create'] = {'type': 'Contracts/Sequential Workflow Operation', 'channel': 'in', 'steps': [
        {'type': 'Contracts/Update Document', 'changeset': [{'op': 'replace', 'path': '/children', 'val': {'$literal': children}}]}]}
    return root
