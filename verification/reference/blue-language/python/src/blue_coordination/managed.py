"""Local authenticated managed admission, inside the closure transaction.

Only histories committed by this host can be imported. Content identity alone
never grants a processing checkpoint or invents a missing historical interval.
"""
from dataclasses import asdict
import hmac
from blue_bex.values import clone, pointer_get, UNDEFINED
from blue_contracts.patch import CapabilityError
from blue_contracts import ContractError
from .errors import Code, require
from .history import Position, Emission, VerifiedTransition, verify_successor


def reject_progress(value):
    if type(value) is dict:
        cs=value.get('contracts')
        if type(cs) is dict and {'initialized','terminated','checkpoint','process','managed','runtime'} & cs.keys():
            raise CapabilityError('authored content cannot assert managed progress; supply an exact retained managed reference')
        for child in value.values():reject_progress(child)
    elif type(value) is list:
        for child in value:reject_progress(child)


class ManagedAdmissions:
    def _event_exact(self,event):
        goal='definition' if self.cat.role(event) in {'initiated_event','terminated_event'} else 'value'
        return self.cat.validate(event,goal=goal)

    def _history_row(self, root, state, *, previous=None, entry=None, receipt=None, events=(), authored=None):
        from .closure import reference_hash, reach
        domain=reach(state.edges,root)
        value={'root':root,'epoch':state.epochs[root],'blueId':state.ids[root],
               'predecessor':None if previous is None else previous['identity'],
               'predecessorBlueId':None if previous is None else previous['blueId'],
               'entry':None if entry is None else entry.blue_id,
               'order':None if entry is None else entry.order.record(),
               'receipt':receipt,'authored':authored,
               'profile':self.profile,'events':clone(list(events)),
               'documents':{n:clone(state.documents[n]) for n in domain},
               'ids':{n:state.ids[n] for n in domain},
               'edges':{n:clone(state.edges[n]) for n in domain},
               'epochs':{n:state.epochs[n] for n in domain},
               'initials':{n:state.initials[n] for n in domain},
               'bases':{n:state.bases[n] for n in domain},
               'channels':{n:clone(state.channels.get(n,())) for n in domain},
               'generations':{n:clone(state.generations.get(n,{})) for n in domain}}
        # Channels are trusted only as part of this host's signed receipt.
        wire={**value,'channels':{n:[asdict(c) for c in cs] for n,cs in value['channels'].items()}}
        value['identity']=reference_hash('blue-python-retained-position/1',wire)
        value['seal']=self._seal({'identity':value['identity'],'profile':self.profile})
        return value

    def _verify_history(self, rows):
        from .closure import reference_hash
        from .model import ExternalOrderKey
        require(bool(rows),Code.NEEDS_RESOURCES,'retained initialization is missing')
        positions=[]
        for row in rows:
            wire={k:v for k,v in row.items() if k not in {'identity','seal'}}
            wire['channels']={n:[asdict(c) for c in cs] for n,cs in wire['channels'].items()}
            require(row['profile']==self.profile and row['identity']==reference_hash('blue-python-retained-position/1',wire)
                    and hmac.compare_digest(row['seal'],self._seal({'identity':row['identity'],'profile':self.profile})),
                    Code.INVALID_EVIDENCE,'retained position signature/profile mismatch')
            for name,tid in row['ids'].items():
                from blue_contracts.catalogue import compact
                require(compact(self.blue.tree(self.blue.get(tid,goal='definition')))==row['documents'][name],
                        Code.INVALID_EVIDENCE,'retained content mismatch')
            emissions=tuple(Emission(i,self._event_exact(e['payload']),e['occurrence']) for i,e in enumerate(row['events']))
            position=Position(row['root'],row['epoch'],0,row['blueId'],row['identity'],row['predecessor'],
                     row['predecessorBlueId'],row['receipt'] or row['identity'],row['entry'] or row['identity'],
                     None if row['order'] is None else ExternalOrderKey.from_record(row['order']),
                     'INITIALIZATION' if not positions else 'REVISION',
                     'INITIALIZATION' if not positions else 'TIMELINE_ENTRY',emissions)
            if positions:
                class VerifiedLocalCommit:
                    def verify(self, previous, successor):
                        return VerifiedTransition(successor.identity,successor.receipt_identity,True)
                verify_successor(positions[-1],position,VerifiedLocalCommit())
            else:
                require(position.epoch==0 and position.predecessor_identity is None and position.predecessor_blue_id is None,
                        Code.INVALID_EVIDENCE,'retained lineage does not start at initialization')
            positions.append(position)
        return tuple(positions)

    def _capture_admissions(self):
        return clone(self.histories)

    def _reconcile(self, stage, parent, before, entry, invocation, meter, captured, schedule):
        from blue_runtime.topology import TopologyState, Occurrence, plan_topology
        from .closure import reference_hash, put, components
        from .identity import history_basis
        paths=self._declared(stage.documents[parent]);old=stage.edges.get(parent,{})
        ledger=stage.generations.setdefault(parent,{p:0 for p in old})
        prior=TopologyState(tuple(Occurrence(p,t,ledger[p]) for p,t in sorted(old.items())),tuple(sorted(ledger.items())))
        requested={};attachments=[]
        for path in paths:
            value=pointer_get(stage.documents[parent],path)
            if value is UNDEFINED:continue
            if path in old and value==pointer_get(before,path):requested[path]=old[path];continue
            meter.charge('closure.admission',amount=50)
            exact=self.cat.validate(value);tid=exact.blue_id
            # Exact IDs (including original authored content) resolve through a
            # retained local admission, never by a user-supplied documentId label.
            found=[]
            for target,rows in captured.items():
                if any(tid in (r['blueId'],r.get('authored')) for r in rows):found.append((target,rows))
            if len(found)>1:raise CapabilityError('ambiguous managed identity; use an exact managed head')
            if found:
                target,rows=found[0];self._verify_history(rows)
                require(all(r['order'] is None or self._order(r['order'])<=entry.order for r in rows),
                        Code.NEEDS_RESOURCES,'retained source is beyond the attachment cutoff')
                selected=rows[-1]
                if target not in stage.documents:
                    for key,field in [('documents','documents'),('ids','ids'),('edges','edges'),('epochs','epochs'),
                                      ('initials','initials'),('bases','bases'),('channels','channels'),('generations','generations')]:
                        for name,v in selected[key].items():
                            if name not in getattr(stage,field):getattr(stage,field)[name]=clone(v)
                attachments.append((path,target,rows))
            else:
                _,body=self.cat.admit(value);reject_progress(body)
                target=body.get('documentId')
                if not isinstance(target,str) or not target or target in captured or target in stage.documents:
                    target='child-'+reference_hash('blue-python-managed-name/1',{'parent':parent,'path':path,
                        'invocation':invocation,'generation':ledger.get(path,-1)+1}).split(':')[1][:24]
                stage.documents[target]=body;stage.edges[target]={};stage.generations[target]={}
                stage.ids[target]=tid;stage.epochs[target]=0;stage.initials[target]=tid
                stage.bases[target]=history_basis({'documentId':target,'initialDocumentBlueId':tid,
                    'runtimeSemanticsIdentity':self.profile,'admission':{'mode':'FULL_HISTORY'}})
                # Prevent nested local processing: all Process Embedded children
                # are independently staged by this same managed transaction.
                initialized=self.processor.process(body,{},initialize_only=True,managed_children=True,gas=meter,
                    read_document=self._reader(stage,target))
                stage.documents[target]=initialized.document
                self._reconcile(stage,target,body,entry,invocation,meter,captured,schedule)
                docs,ids=self.finalize({n:stage.documents[n] for n in self._reachable(stage,target)},stage.edges)
                stage.documents.update(docs);stage.ids.update(ids);stage.initials[target]=ids[target]
                stage.bases[target]=history_basis({'documentId':target,'initialDocumentBlueId':ids[target],
                    'runtimeSemanticsIdentity':self.profile,'admission':{'mode':'FULL_HISTORY'}})
                stage.channels[target]=self._compile_new(stage,target,entry)
                initial_events=[]
                for i,event in enumerate(initialized.events):
                    event_id=self._event_exact(event).blue_id
                    initial_events.append({'source':target,'blueId':event_id,'payload':event,
                        'occurrence':reference_hash('blue-python-initialization-event/1',{'target':target,'initial':ids[target],'ordinal':i})})
                row=self._history_row(target,stage,events=initial_events,authored=tid)
                stage.births[target]=row
                captured[target]=[row]
                attachments.append((path,target,[row]))
            requested[path]=target
        plan=plan_topology(prior,requested)
        if plan.edits:
            previous_edges={**stage.edges,parent:old}
            group=next(g for g in components(stage.documents,previous_edges) if parent in g)
            if len(group)>1 or parent in old.values():
                raise CapabilityError('changing an existing cyclic ownership cohort requires an explicit graph admission')
        stage.edges[parent]=requested;stage.generations[parent]=dict(plan.after.generations)
        for edit in plan.edits:
            if edit.after and parent in self._reachable(stage,edit.after.target):
                raise CapabilityError('dynamic admission into a new cyclic ownership group requires an explicit graph admission')
        for path,target,rows in attachments:
            generation=stage.generations[parent][path]
            # An unchanged binding does not replay history just because an
            # operation repeated the same reference.
            if not any(e.after and e.after.path==path for e in plan.edits):continue
            for row in (rows if self.attachment_mode=='FULL_HISTORY' or target in stage.births else []):
                for event in row['events']:
                    schedule(parent,path,event['payload'],row['documents'])
            stage.catchups[parent+path]={'parent':parent,'path':path,'target':target,'generation':generation,
                'status':'ACTIVE','mode':self.attachment_mode,
                'appliedEpochs':len(rows)-1 if self.attachment_mode=='FULL_HISTORY' else 0,
                'requiredEpochs':len(rows)-1 if self.attachment_mode=='FULL_HISTORY' else 0,
                'capturedGoal':rows[-1]['identity'],'sourceBlueId':rows[-1]['blueId']}
        for edit in plan.edits:
            if edit.kind=='remove':stage.catchups.pop(parent+edit.before.path,None)
        for path,target in requested.items():stage.documents[parent]=put(stage.documents[parent],path,{'blueId':stage.ids[target]})

    @staticmethod
    def _order(record):
        from .model import ExternalOrderKey
        return ExternalOrderKey.from_record(record)

    @staticmethod
    def _reachable(stage,root):
        from .closure import reach
        return reach(stage.edges,root)

    def _compile_new(self,stage,n,entry):
        from .compiler import compile_channels
        return compile_channels(self.blue,self.registry,self.blue.get(stage.ids[n],goal='definition'),n,stage.bases[n],
            old=stage.channels.get(n,()),creating_entry=entry,trusted_checkpoint=True)[0]
