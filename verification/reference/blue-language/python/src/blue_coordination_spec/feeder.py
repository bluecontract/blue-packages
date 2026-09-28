"""Verified-prefix feeding over the three-input Contracts boundary."""
from algorithms import blue as L
from blue_contracts import ContractError
from .model import Decision, CoordinationError, PlannedEvent, require, uint
from .evidence import CoordinationEvidence
from .planning import acquire, first_relevant

class Coordinator:
    def __init__(self,processor,catalogue,providers):
        self.processor,self.catalogue,self.providers=processor,catalogue,providers
        self._issued={}
    def next(self,snapshot,*,before,instances=None,port_owners=None):
        from blue_contracts.reference.model import SAFE
        uint(before,SAFE+1);selected=None
        try:
            graph,prefixes,lookup=acquire(self.processor,snapshot,self.providers,before)
            entries=[e for p in prefixes for e in p.entries if e.timestamp<before]
            evidence=CoordinationEvidence(prefixes,lookup=lookup,
                bindings={'snapshot':snapshot.identity,'before':str(before)})
            for selected,recipients in first_relevant(self.processor,snapshot,graph,entries,evidence):
                # The old Contracts Grant/Operation Port protocol is not part of
                # this release. Never silently turn an unverified mandate into permission.
                require(selected.authority is None,'UNSUPPORTED_LEGACY_MANDATE')
                plan=PlannedEvent(snapshot.identity,evidence.resolve(selected.blue_id),recipients)
                decision=Decision('READY',snapshot.identity,selected.blue_id,plan,evidence,
                    audit={'before':str(before),'prefixes':[p.wire() for p in prefixes],
                           'authority':[{'mode':'PROVIDER_APPEND_ACL'}],
                           'proofRecords':{p.proof:self.providers.verifier.packages[p.proof] for p in prefixes}})
                self._issued[decision.identity]=decision.wire()
                return decision
            return Decision('IDLE_THROUGH',snapshot.identity,
                audit={'before':str(before),'prefixes':[p.wire() for p in prefixes]})
        except (CoordinationError,ContractError) as error:
            code=error.code;details=getattr(error,'details',getattr(error,'context',{}))
            status=('WAITING' if code in {'DEFERRED_UNAVAILABLE','NOT_FOUND','NEEDS_RESOURCES','NEEDS_SOURCE_EVIDENCE'}
                    else 'UNSUPPORTED' if code.startswith('UNSUPPORTED') or code=='UNBOUND_COORDINATION_CHANNEL' else 'BLOCKED')
            return Decision(status,snapshot.identity,selected.blue_id if selected else None,
                            diagnostic={'code':code,**details})
    def execute(self,snapshot,decision,*,gas_limit=100000,local_limits=None):
        require(decision.status=='READY' and decision.snapshot==snapshot.identity,'NOT_READY')
        require(self._issued.get(decision.identity)==decision.wire(),'UNISSUED_DECISION')
        # Configuration, not extra processor arguments.
        from blue_contracts.reference.model import integer
        self.processor.gas_limit=integer(gas_limit,0,100000)
        self.processor.local_limits=dict(local_limits or {})
        return self.processor.process(snapshot,L.Ref(decision.entry),decision.plan.envelope.timestamp)
    def run(self,snapshot,*,before,max_events=1000,gas_limit=100000,instances=None,port_owners=None,local_limits=None):
        uint(max_events);outcomes=[]
        for _ in range(max_events):
            decision=self.next(snapshot,before=before,instances=instances,port_owners=port_owners)
            if decision.status!='READY':return snapshot,outcomes,decision
            outcome=self.execute(snapshot,decision,gas_limit=gas_limit,local_limits=local_limits)
            outcomes.append((decision,outcome))
            if not outcome.commits:
                return snapshot,outcomes,Decision('BLOCKED',snapshot.identity,decision.entry,
                    diagnostic={'code':outcome.status,'processor':outcome.diagnostic})
            snapshot=outcome.snapshot
        return snapshot,outcomes,Decision('TURN_LIMIT',snapshot.identity,audit={'completed':len(outcomes),'before':str(before)})
