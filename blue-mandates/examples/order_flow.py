"""Example authoring composition; all state/authority execution is packaged BEX/Coordination."""
from session import operation,change,workflow


def order(s):
    # Two ordinary example Event subtypes, not native authority extensions.
    events={label:s.engine.publish_content({'name':'Example/Order '+label,
        'type':s.hub.catalogue.typed('Event')['type']}) for label in ('Approved','Released')}
    def transition(before,after,label):
        return [ {'$failIf':{'cond':{'$ne':[{'$document':'/phase'},before]},'message':'WRONG_ORDER_PHASE'}},
            change('/phase',after),{'$appendEvent':{'$literal':{'type':{'blueId':events[label]}}}} ]
    t=s.add({'name':'Example Order JH-042','phase':'Proposed','currency':'EUR','total':840,
        'contracts':{'sellerChannel':s.channel('holder'),'agentChannel':s.channel('agent'),
            'approveOrder':operation('sellerChannel',[{'$failIf':{'cond':{'$ne':[{'$keys':{'$binding':'call/request'}},[]]},'message':'EMPTY_REQUEST'}},*transition('Proposed','Approved','Approved')]),
            'releaseForFulfilment':operation('sellerChannel',[
                {'$failIf':{'cond':{'$ne':[{'$keys':{'$binding':'call/request'}},['method']]},'message':'ONLY_METHOD'}},
                *transition('Approved','Released','Released')],{'method':'standard'})}})
    return t,events


def grants(s,t):
    initial={'blueId':s.row(t)['documentId']}
    approve=s.typ('Operation Grant',target={'initialDocument':initial,'channel':'sellerChannel','operation':'approveOrder',
        'documentValidation':{'document':s.typ('Pattern',valueType={
            'phase':'Proposed','currency':'EUR','total':{'type':'Integer','schema':{'required':True}}}),
            'function':{'expr':{'$and':[{'$gt':[{'$binding':'targetDocument/total'},0]},
                                      {'$lte':[{'$binding':'targetDocument/total'},1000]}]}}}},
        validation={'function':{'expr':{'$eq':[{'$keys':{'$binding':'request'}},[]]}}})
    release=s.typ('Operation Grant',target={'initialDocument':initial,'channel':'sellerChannel','operation':'releaseForFulfilment',
        'documentValidation':{'document':{'phase':'Approved'}}},
        validation={'request':{'method':'standard'},'function':{'expr':{'$eq':[{'$keys':{'$binding':'request'}},['method']]}}})
    return approve,release


def mandate(s,t,events,*,connected=True,qualified=False):
    approve,release=grants(s,t)
    src=s.mandate_source({'approve':approve} if not qualified else {},
        type_name='Qualification Mandate' if qualified else 'Operation Mandate',
        grantTemplates={'approve':approve,'release':release})
    if qualified:
        src.update(evidenceRequirement={'operationId':'customer-qualification','operationRevision':1,
            'document':{'blueId':s.row(t)['documentId']}},scopeOnSuccess={'approve':approve})
        src['contracts']['evidenceProviderChannel']=s.channel('provider')
    else:src['stage']='ApprovalEnabled'
    def terminate(reason):return {'$appendEvent':{'$literal':s.typ('Mandate Termination Requested',reason=reason)}}
    if connected:
        src['target']={'blueId':s.row(t)['lastStable']['blueId']}
        src['contracts'].update(
            embedded={'type':'Contracts/Process Embedded','paths':['/target']},
            approvedEvents={'type':'Contracts/Embedded Node Channel','sourcePath':'/target','event':{'type':{'blueId':events['Approved']}}},
            releasedEvents={'type':'Contracts/Embedded Node Channel','sourcePath':'/target','event':{'type':{'blueId':events['Released']}}},
            afterApproved=workflow('approvedEvents',{},[
                {'$if':{'cond':{'$and':[{'$eq':[{'$document':'/status'},'Active']},
                    {'$eq':[{'$document':'/stage'},'EvidencePassed' if qualified else 'ApprovalEnabled']},
                    {'$eq':[{'$document':'/target/phase'},'Approved']}]},
                    'then':[change('/scope',{'release':{'$document':'/grantTemplates/release'}}),change('/stage','ReleaseEnabled')],
                    'else':[terminate('Order advanced outside this delegation stage.')]}}]),
            afterReleased=workflow('releasedEvents',{},[
                change('/stage','Finished'),terminate('Order released; delegation complete.')]))
    else:
        src['contracts']['acknowledgeOrderApproval']=operation('authorityHolderChannel',[
            {'$failIf':{'cond':{'$ne':[{'$document':'/status'},'Active']},'message':'NOT_ACTIVE'}},
            {'$failIf':{'cond':{'$ne':[{'$document':'/stage'},'ApprovalEnabled']},'message':'WRONG_STAGE'}},
            {'$failIf':{'cond':{'$ne':[{'$keys':{'$binding':'call/request'}},[]]},'message':'EMPTY_REQUEST'}},
            change('/scope',{'release':{'$document':'/grantTemplates/release'}}),change('/stage','ReleaseEnabled')])
    return s.add(src)
