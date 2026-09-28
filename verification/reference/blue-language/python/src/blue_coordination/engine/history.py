"""Established lineage, pre-action authority and exact history selection."""
from algorithms import blue as L
from blue_bex import Context, BexError
from blue_coordination_spec.model import require, CoordinationError
from .source_records import entries as source_entries, StoredEntries
from .sources import VerifiedPrefix


class HistoryResolver:
    def __init__(self, catalogue, context='default'):
        self.catalogue, self.context = catalogue, context
        self.view = None

    def bind(self, view):
        self.view = view

    def key(self, identity):
        return self.context + '/' + identity

    def terminal(self, lineage, member, channel, generation, entry):
        from .dispositions import key, validate
        from .store import fingerprint
        if self.view is None or getattr(self, 'receiving_instance', None) is None:return False
        found = self.view.get('terminal_inputs', key(self.receiving_instance, member, channel, generation, entry))
        if found is None:return False
        row = self.view.get('input_dispositions', found['decision'])
        require(row is not None, 'CORRUPT_INPUT_DISPOSITION')
        validate(row)
        require(fingerprint(row) == found['decision'] and row['instance'] == self.receiving_instance and row['entry'] == entry and
            dict(member=member, channel=channel, generation=generation) in row['scope'], 'CORRUPT_INPUT_DISPOSITION')
        return True

    def retained_prefix(self, proof, trusted):
        if self.view is None:return None
        row=self.view.get('source_proofs',proof)
        if row is None:return None
        require(row['timeline'] in trusted, 'UNTRUSTED_PROVIDER')
        return VerifiedPrefix(row['timeline'],row['before'],StoredEntries(self.view,row['timeline'],row['count']),
                              row['guarantee'],row['attestation'])

    def lineage(self, member, identity):
        row = self.view.project('versions', self.key(identity), ('documentId', 'member'))
        return row['documentId'] if row and row['member'] == member else None

    def belongs(self, lineage, identity):
        if identity == lineage:
            return self.view.get('binding', self.key(lineage)) is not None
        self.view._check()
        projections=getattr(self.view,'_projections',None)
        if projections is None: projections=self.view._projections={}
        key=('lineage',self.context,identity)
        if key not in projections:
            row=self.view.project('versions',self.key(identity), ('documentId',))
            projections[key]=row['documentId'] if row is not None else None
        return projections[key] is not None and projections[key] == lineage

    def known(self, identity):
        return self.view.project('versions',self.key(identity), ()) is not None or self.view.get('binding',self.key(identity)) is not None

    def before(self, lineage, order):
        binding = self.view.get('binding', self.key(lineage))
        require(binding is not None, 'WAITING_AUTHORITY_HISTORY', document=lineage)
        instance = binding['instance']
        head = self.view.project('heads', instance, ('context',))
        key = (order.timestamp, order.source, order.event)
        require(head is not None and self.complete_before(instance, key),
            'WAITING_AUTHORITY_COMPLETENESS', document=lineage, instance=instance)
        selected = self.view.history_before(instance, key)
        require(selected is not None, 'WAITING_AUTHORITY_HISTORY', document=lineage)
        return selected

    def complete_before(self, instance, key, visiting=None):
        """Prove a strict prefix without consuming the candidate itself.

        Source coverage, examined direct work and installed child history are
        independent facts. A future receipt is sufficient evidence of earlier
        examination; otherwise inspect only the open strict prefix. Cycles in
        the read graph do not require processing the candidate to authorize it.
        """
        visiting = set() if visiting is None else visiting
        if instance in visiting:
            return True
        visiting.add(instance)
        head = self.view.project('heads', instance, ('terminated', 'lastOrder', 'checkedBoundary',
                                'sourceTimelines', 'channels', 'attachmentGoals', 'rebaseGoals'))
        if head is None:
            return False
        # Worker state is not prefix evidence. Reading a consumer's changing
        # lease/fence/status here makes its harmless polls invalidate a producer
        # that is using already established pre-action authority. Unresolved
        # earlier work is detected below from exact source/history obligations;
        # a later or unscoped worker diagnostic cannot revoke an earlier proof.
        examined = tuple(head.get('lastOrder') or (-1, '', ''))
        if not head.get('terminated') and examined < key and head.get('checkedBoundary', 0) <= key[0]:
            timelines = set(head.get('sourceTimelines', [r['timeline'] for r in head['channels']]))
            for actor in {r['actor'] for r in head['channels']}:
                timelines.update(row['timeline'] for _, row in self.view.scan('authority_sources', self.context + '/' + actor + '/'))
            for timeline in timelines:
                source = self.view.get('sources', timeline)
                if source is None or source['before'] <= key[0] or self.view.get('source_issues', timeline):
                    return False
                if source_entries(self.view, timeline, source, after=examined, before=key, limit=1):
                    return False
        for goal in head.get('attachmentGoals', {}).values():
            if goal.get('activationOrder') is None or tuple(goal['activationOrder']) < key:
                return False
        if any(tuple(g['cutoff']) < key for g in head.get('rebaseGoals', [])):
            return False
        for _, edge in self.view.scan('forward', instance + '/'):
            source = edge['source']
            selected = self.view.project('versions', self.key(edge['selected']), ('number',))
            if selected is None:
                return False
            successor = self.view.get('history', source + '/' + str(selected['number'] + 1).zfill(16))
            if successor and (successor.get('effectiveOrder') is None or tuple(successor['effectiveOrder']) < key):
                return False
            if not self.complete_before(source, key, visiting):
                return False
        return True

    def actor_policy(self, target, operation, entry, *, delegated):
        c = self.catalogue
        contracts = c.processor.registry.contracts(L.Ref(target))
        actor_kind = 'principal' if c.is_type(L.Ref(entry.actor), 'Principal Actor') else 'agent'
        source_kind = None
        if entry.source:
            for label, name in (('browserSession', 'Browser Session Source'), ('apiCall', 'API Call Source'), ('documentRequest', 'Document Request Source')):
                if c.is_type(L.Ref(entry.source), name):
                    source_kind = label
                    break
        for declaration in contracts.values():
            extension = declaration.get('_extension')
            if extension is None or extension.binding.type_id != c.types['Coordination/Actor Policy']:
                continue
            # Read authored policy operands, not the executable template's raw
            # typed dictionary (which also contains Language type metadata).
            exact = c.blue.exact(declaration['_recipe']); c.blue.remember(exact)
            operand = c.operand(c.blue.identity(exact), 'operations')
            policies = c._values(operand) if operand is not None else {}
            restrictions = policies.get(operation)
            if restrictions is None:
                continue
            require(set(restrictions) <= {'requiresActor', 'requiresSource', 'excludeSource', 'allowsDelegation'}, 'INVALID_ACTOR_POLICY')
            if restrictions.get('requiresActor', 'any') not in ('any', actor_kind):
                return False
            if 'requiresSource' in restrictions and restrictions['requiresSource'] != source_kind:
                return False
            if 'excludeSource' in restrictions and restrictions['excludeSource'] == source_kind:
                return False
            if delegated and restrictions.get('allowsDelegation') is False:
                return False
        return True

    def _predicate(self, mandate, validation, candidate, field, binding):
        c, p = self.catalogue, self.catalogue.processor
        expected = 'Mandate/Document Validation' if field == 'document' else 'Mandate/Request Validation'
        c.read(validation, expected)
        pattern = c.operand(validation, field)
        if pattern is not None and not p.blue.matches(candidate, pattern):
            return False
        function = c.operand(validation, 'function')
        if function is not None:
            program = p.blue.bex_data(function)
            try:
                result = p.bex.execute(program, Context(document=p.blue.view(L.Ref(mandate)),
                    bindings={binding: p.blue.view(candidate)}))
            except BexError as error:
                raise CoordinationError('INVALID_AUTHORITY_PREDICATE', detail=str(error)) from error
            require(not result.changeset and not result.events and type(result.value) is bool, 'INVALID_AUTHORITY_PREDICATE')
            if not result.value:
                return False
        return True

    def authorize(self, entry, lineage, target, channel, holder, request):
        c = self.catalogue
        c.read(entry.authority, 'Mandate/Mandate Authority')
        represented = c.link(entry.authority, 'actor')
        if represented != holder:
            return dict(disposition='DENIED', reason='Authority represents another holder')
        initial = c.link(entry.authority, 'mandate')
        # The authority link names the initial document, never a convenient
        # caller-selected later scope. The binding is established by processing.
        binding = self.view.get('binding', self.key(initial))
        require(binding is not None, 'WAITING_AUTHORITY_HISTORY', document=initial)
        position = self.before(initial, entry.order)
        mandate = position['document']
        c.read(mandate, 'Mandate/Operation Mandate', closed=False)
        body = L.Ref(mandate)
        if c.blue.read(body, '/status') != 'Active':
            return dict(disposition='DENIED', reason='Mandate is not Active at the pre-action order key')
        require(position.get('approvedProgram') is not None, 'UNESTABLISHED_MANDATE_APPROVAL')
        contracts = c.processor.registry.contracts(body)
        holder_channel = contracts.get('authorityHolderChannel')
        delegate_channel = contracts.get('authorizedActorChannel')
        require(holder_channel is not None and delegate_channel is not None, 'INVALID_MANDATE_PARTICIPANTS')
        holder_id = c.blue.identity(c.blue.exact(holder_channel['_recipe']))
        delegate_id = c.blue.identity(c.blue.exact(delegate_channel['_recipe']))
        if c.link(holder_id, 'actor') != holder or c.link(delegate_id, 'actor') != entry.actor or c.link(delegate_id, 'timeline') != entry.timeline:
            return dict(disposition='DENIED', reason='The actual actor is not this Mandate’s authorized participant')
        scope = c.operand(mandate, 'scope')
        require(scope is not None, 'INVALID_MANDATE_SCOPE')
        for key in sorted(c.blue.head(scope).fields):
            grant = c.operand(c.blue.identity(scope), key)
            grant_id = c.blue.identity(grant)
            c.blue.remember(grant)
            c.read(grant_id, 'Mandate/Operation Grant')
            target_spec = c.operand(grant_id, 'target')
            if c.blue.read(grant, '/target/channel') != channel or c.blue.read(grant, '/target/operation') != request['operation']:
                continue
            raw_target = target_spec
            raw_target_id = c.blue.identity(raw_target)
            c.blue.remember(raw_target)
            pinned = c.link(raw_target_id, 'initialDocument', optional=True)
            if pinned is not None and pinned != lineage:
                continue
            document_validation = c.link(raw_target_id, 'documentValidation', optional=True)
            if document_validation is not None and not self._predicate(mandate, document_validation, L.Ref(target), 'document', 'targetDocument'):
                continue
            validation = c.link(grant_id, 'validation', optional=True)
            if validation is not None:
                if 'request' not in request or not self._predicate(mandate, validation, L.Ref(request['request']['blueId']), 'request', 'request'):
                    continue
            return dict(disposition='ELIGIBLE', reason='One complete approved scope grant matches',
                        grantKey=key, mandatePosition=position['position'])
        return dict(disposition='DENIED', reason='No single complete scope grant matches this action')
