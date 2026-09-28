"""Author data-only Blue packages. Helpers below assemble BEX, never execute it.
The business transitions live exclusively in the exported .blue definitions.
"""
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[1]

def op(k,v):return {k:v}
def V(n,p=''):return op('$var',{'name':n,'path':p}) if p else op('$var',n)
def D(p):return op('$document',p)
def C(n,p=''):return op('$const',{'name':n,'path':p}) if p else op('$const',n)
def eq(a,b):return op('$eq',[a,b])
def ne(a,b):return op('$ne',[a,b])
def AND(*v):return op('$and',list(v))
def OR(*v):return op('$or',list(v))
def NOT(v):return op('$not',v)
def kind(v,k):return op('$isKind',{'val':v,'kind':k})
def has(v,k):return op('$hasKey',{'object':v,'key':k})
def get(v,k):return op('$get',{'object':v,'key':k})
def choose(c,a,b):return op('$choose',{'cond':c,'then':a,'else':b})
def objset(v,k,x):return op('$objectSet',{'object':v,'key':k,'val':x})
def let(n,x):return op('$let',{'name':n,'expr':x})
def SET(n,x):return op('$set',{'name':n,'expr':x})
def put(k,x):return SET('s',objset(V('s'),k,x))
def iff(c,t,e=None):return op('$if',{'cond':c,'then':t,**({'else':e} if e is not None else {})})
def need(c,m):return op('$failIf',{'cond':NOT(c),'message':m})
def call(n,**args):return op('$call',{'function':n,**({'args':args} if args else {})})
def ret(x):return op('$return',x)
def digest(x):return op('$nodeBlueId',x)
def emit(x):return op('$appendEvent',x)
def patch(path,val,operation='replace'):return op('$appendChange',{'op':operation,'path':path,**({'val':val} if operation!='remove' else {})})
def typed(t,**fields):return {'type':t,**fields}
def msg(prototype,body):return objset(body,'type',C('messageTypes','/'+prototype+'/type'))
def field(t):return {'type':t}
def signal_record(s):return {'decision':s,'party':V('side'),'round':V('s','/round'),'termsId':V('s','/targetId'),
    'requestId':V('req','/requestId'),'eventId':digest(op('$event',''))}
def set_signal(value):return [put('signals',objset(V('s','/signals'),V('side'),value)),
    put('records',objset(V('s','/records'),V('side'),signal_record(value)))]
def clear_signals():return [put('signals',{'A':'NONE','B':'NONE'}),put('records',{'A':{},'B':{}})]
def new_round():return [put('round',op('$add',[V('s','/round'),1])),*clear_signals()]
def signal_from_intention():return [iff(ne(V('intent'),'NONE'),set_signal(V('intent')))]
def decision(result):return emit(msg('decision',{'inResponseTo':objset({},'blueId',digest(V('s','/proposal'))),'recipientChannel':op('$concat',['party',V('other')]),'result':result,
    'message':op('$default',[V('req','/message'),'']),'decidedBy':V('side'),'requestId':V('req','/requestId')}))
def reset_to_settled():return [put('pending',False),put('proposal',{}),put('proposer',''),put('target',V('s','/settled')),
    put('targetId',call('revision',terms=V('s','/settled'))),*new_round()]


def program_guard(allowed, static):
    return [need(op('$isEmpty',op('$filter',{'in':op('$keys',D('/contracts')),'item':'key',
        'where':NOT(op('$includes',{'list':op('$listConcat',[D('/type/declaredContracts'),['initialized','checkpoint','terminated']]),'val':V('key')}))})),'UNAPPROVED_CONTRACT_DECLARATION'),
        op('$forEach',{'in':D('/type/declaredContracts'),'item':'guardContract','do':[
            iff(NOT(op('$includes',{'list':['partyA','partyB'],'val':V('guardContract')})),[
                need(eq(digest(D(op('$concat',['/contracts/',V('guardContract')]))),
                        digest(D(op('$concat',['/type/contracts/',V('guardContract')])))),
                     'EXECUTABLE_OVERRIDE_NOT_ALLOWED')])
        ]})]

def make_clause():
    # Revision binds contractual content to immutable agreement/party/program/channel choices.
    revision={'args':{'terms':{}},'expr':digest({'agreementId':D('/agreementId'),
        'agreementType':D('/agreementType'),'activationType':digest(D('/type')),
        'partyA':D('/partyA'),'partyB':D('/partyB'),
        'channelA':D('/contracts/partyA'),'channelB':D('/contracts/partyB'),
        'terms':V('terms')})}
    initial=program_guard(['partyA','partyB','lifecycle','initialize','actA','actB','logic'],['lifecycle','initialize','actA','actB','logic'])+[need(kind(D('/agreementId'),'text'),'AGREEMENT_ID_REQUIRED'),
        need(ne(D('/agreementId'),''),'AGREEMENT_ID_REQUIRED'),
        need(ne(digest(D('/partyA')),digest(D('/partyB'))),'TWO_DISTINCT_PARTIES_REQUIRED'),
        need(eq(digest(D('/contracts/partyA/actor')),digest(D('/partyA'))),'PARTY_A_CHANNEL_MISMATCH'),
        need(eq(digest(D('/contracts/partyB/actor')),digest(D('/partyB'))),'PARTY_B_CHANNEL_MISMATCH'),
        need(kind(D('/initialTerms'),'object'),'TERMS_MUST_BE_OBJECT'),
        patch('/state',{'phase':'NEGOTIATING','round':1,'settled':D('/initialTerms'),'target':D('/initialTerms'),
            'targetId':call('revision',terms=D('/initialTerms')),'pending':False,'proposal':{},'proposer':'',
            'signals':{'A':'NONE','B':'NONE'},'records':{'A':{},'B':{}},'seen':{},'consent':{},'message':''},'add'),
        emit(msg('progress',{'agreementId':D('/agreementId'),'reason':'INITIALIZED'}))]
    common=[let('req',op('$binding','call/request')),need(kind(V('req'),'object'),'REQUEST_REQUIRED'),
        need(kind(V('req','/requestId'),'text'),'REQUEST_ID_REQUIRED'),need(ne(V('req','/requestId'),''),'REQUEST_ID_REQUIRED'),
        let('s',D('/state')),let('reqHash',digest(V('req'))),
        let('seenKey',op('$concat',[V('side'),':',V('req','/requestId')])),
        iff(has(V('s','/seen'),V('seenKey')),[need(eq(get(V('s','/seen'),V('seenKey')),V('reqHash')),'REQUEST_ID_REUSE'),ret(True)]),
        need(eq(V('s','/phase'),'NEGOTIATING'),'NEGOTIATION_CLOSED'),
        need(eq(V('req','/round'),V('s','/round')),'STALE_ROUND'),
        need(eq(V('req','/termsId'),V('s','/targetId')),'STALE_TERMS'),
        let('action',V('req','/action')),let('other',choose(eq(V('side'),'A'),'B','A')),
        need(op('$includes',{'list':['proposeChange','acceptChange','rejectChange','withdrawChange','ready','approve','withdrawApproval','rejectApproval','decline'],'val':V('action')}),'UNKNOWN_ACTION'),
        let('intent',op('$default',[V('req','/intention'),'NONE'])),
        need(op('$includes',{'list':['NONE','READY','APPROVED'],'val':V('intent')}),'INVALID_INTENTION'),
        need(OR(op('$includes',{'list':['proposeChange','acceptChange'],'val':V('action')}),eq(V('intent'),'NONE')),'INTENTION_ONLY_ON_EDIT_COMMANDS'),
        need(op('$isEmpty',op('$filter',{'in':op('$keys',V('req')),'item':'key',
           'where':NOT(op('$includes',{'list':['type','action','requestId','round','termsId','message','intention','changes','proposalId'],'val':V('key')}))})),'UNKNOWN_REQUEST_FIELD'),
        need(OR(NOT(has(V('req'),'message')),kind(V('req','/message'),'text')),'MESSAGE_MUST_BE_TEXT')]
    # Patches are applied to a local terms value, NEVER to the managed document.
    propose=[need(kind(V('req','/message'),'text'),'EXPLANATION_REQUIRED'),need(ne(V('req','/message'),''),'EXPLANATION_REQUIRED'),
        need(kind(V('req','/changes'),'list'),'CHANGES_REQUIRED'),need(op('$gt',[op('$size',V('req','/changes')),0]),'CHANGES_REQUIRED'),
        let('candidate',V('s','/settled')),
        op('$forEach',{'in':V('req','/changes'),'item':'change','do':[
            need(kind(V('change'),'object'),'INVALID_PATCH'),
            need(op('$includes',{'list':['set','remove'],'val':V('change','/op')}),'INVALID_PATCH_OP'),
            need(kind(V('change','/path'),'text'),'INVALID_PATCH_PATH'),
            need(OR(eq(V('change','/path'),''),op('$startsWith',[V('change','/path'),'/'])),'INVALID_PATCH_PATH'),
            need(op('$isEmpty',op('$filter',{'in':op('$keys',V('change')),'item':'key','where':NOT(op('$includes',{'list':['op','path','val'],'val':V('key')}))})),'UNKNOWN_PATCH_FIELD'),
            need(eq(has(V('change'),'val'),ne(V('change','/op'),'remove')),'PATCH_VALUE_MISMATCH'),
            need(eq(op('$size',op('$split',{'text':V('change','/path'),'separator':'~'})),1),'ESCAPED_PATH_USE_ROOT_REPLACEMENT'),
            iff(AND(ne(V('change','/path'),''),ne(V('change','/path'),'/')),[
                let('parts',op('$split',{'text':V('change','/path'),'separator':'/'})),let('at',V('candidate')),
                op('$forEach',{'in':V('parts'),'item':'part','index':'index','do':[
                    iff(op('$gt',[V('index'),0]),[
                        need(kind(V('at'),'object'),'EDIT_PARENT_MUST_BE_OBJECT'),
                        iff(op('$lt',[V('index'),op('$subtract',[op('$size',V('parts')),1])]),[
                            need(has(V('at'),V('part')),'EDIT_PARENT_MISSING'),SET('at',get(V('at'),V('part')))
                        ],[iff(eq(V('change','/op'),'remove'),[need(has(V('at'),V('part')),'REMOVE_TARGET_MISSING')])])
                    ])
                ]})
            ],[need(eq(V('change','/op'),'set'),'CANNOT_REMOVE_TERMS_ROOT')]),
            SET('candidate',op('$pointerSet',{'object':V('candidate'),'path':V('change','/path'),'op':V('change','/op'),'val':V('change','/val')}))]}),
        need(kind(V('candidate'),'object'),'TERMS_MUST_BE_OBJECT'),
        need(ne(digest(V('candidate')),digest(V('s','/settled'))),'NO_CHANGE'),
        iff(V('s','/pending'),[decision('SUPERSEDED')]),*new_round(),
        put('target',V('candidate')),put('targetId',call('revision',terms=V('candidate'))),put('pending',True),put('proposer',V('side')),
        put('proposal',msg('proposal',{'requestId':V('req','/requestId'),'agreementId':D('/agreementId'),
            'recipientChannel':op('$concat',['party',V('other')]),'proposedBy':V('side'),'round':V('s','/round'),'termsId':V('s','/targetId'),
            'explanation':V('req','/message'),'changes':V('req','/changes'),'candidate':V('candidate')})),
        *signal_from_intention(),emit(V('s','/proposal'))]
    check_proposal=[need(V('s','/pending'),'NO_PENDING_CHANGE'),need(eq(V('req','/proposalId'),digest(V('s','/proposal'))),'STALE_PROPOSAL')]
    accept=[*check_proposal,need(ne(V('side'),V('s','/proposer')),'PROPOSER_CANNOT_ACCEPT_OWN_CHANGE'),
        decision('ACCEPTED'),put('settled',V('s','/target')),put('pending',False),put('proposal',{}),put('proposer',''),*signal_from_intention()]
    reject=[*check_proposal,need(ne(V('side'),V('s','/proposer')),'PROPOSER_MUST_WITHDRAW'),
        need(kind(V('req','/message'),'text'),'REASON_REQUIRED'),need(ne(V('req','/message'),''),'REASON_REQUIRED'),
        decision('REJECTED'),*reset_to_settled()]
    withdraw=[*check_proposal,need(eq(V('side'),V('s','/proposer')),'ONLY_PROPOSER_CAN_WITHDRAW'),decision('WITHDRAWN'),*reset_to_settled()]
    ready=set_signal('READY') # An existing binding approval cannot silently be downgraded.
    ready=[need(ne(get(V('s','/signals'),V('side')),'APPROVED'),'WITHDRAW_APPROVAL_FIRST'),*ready]
    approve=[need(OR(NOT(V('s','/pending')),eq(V('side'),V('s','/proposer'))),'ACCEPT_CHANGE_FIRST'),*set_signal('APPROVED')]
    withdraw_approval=[need(ne(get(V('s','/signals'),V('side')),'NONE'),'NO_OWN_SIGNAL'),*new_round()]
    reject_approval=[need(eq(get(V('s','/signals'),V('other')),'APPROVED'),'NO_OTHER_APPROVAL'),
        need(kind(V('req','/message'),'text'),'REASON_REQUIRED'),need(ne(V('req','/message'),''),'REASON_REQUIRED'),*new_round()]
    decline=[need(kind(V('req','/message'),'text'),'REASON_REQUIRED'),need(ne(V('req','/message'),''),'REASON_REQUIRED'),
        iff(V('s','/pending'),[decision('DECLINED')]),*reset_to_settled(),put('phase','DECLINED')]
    actions={'proposeChange':propose,'acceptChange':accept,'rejectChange':reject,'withdrawChange':withdraw,
        'ready':ready,'approve':approve,'withdrawApproval':withdraw_approval,'rejectApproval':reject_approval,'decline':decline}
    tail=[put('message',op('$default',[V('req','/message'),''])),
        iff(AND(NOT(V('s','/pending')),eq(V('s','/signals/A'),'APPROVED'),eq(V('s','/signals/B'),'APPROVED')),[
            put('phase','CONSENTED'),put('consent',{'termsId':V('s','/targetId'),'round':V('s','/round'),'approvals':V('s','/records')})]),
        put('seen',objset(V('s','/seen'),V('seenKey'),V('reqHash'))),patch('/state',V('s')),
        emit(msg('progress',{'agreementId':D('/agreementId'),'reason':V('action'),'requestId':V('req','/requestId')})),
        emit(msg('transition',{'agreementId':D('/agreementId'),'action':V('action'),'party':V('side'),'round':V('s','/round'),'termsId':V('s','/targetId'),'requestId':V('req','/requestId')})),
        iff(eq(V('s','/phase'),'CONSENTED'),[emit(msg('succeeded',{'agreementId':D('/agreementId'),'round':V('s','/round'),'termsId':V('s','/targetId'),'requestId':V('req','/requestId')}))]),
        iff(eq(V('s','/phase'),'DECLINED'),[emit(msg('declined',{'agreementId':D('/agreementId'),'message':V('s','/message'),'requestId':V('req','/requestId')}))])]
    return {'name':'Mutual Activation Clause','type':'Agreements/Clause',
        'declaredContracts':['partyA','partyB','lifecycle','initialize','actA','actB','logic'],
        'description':'Bilateral pre-activation negotiation. All behavior is ordinary Contracts/BEX; readiness is non-binding.',
        'contracts':{
            'partyA':typed('Coordination/Timeline Channel'), 'partyB':typed('Coordination/Timeline Channel'),
            'lifecycle':typed('Contracts/Lifecycle Event Channel',event={'type':'Contracts/Document Processing Initiated'}),
            'initialize':typed('Contracts/Sequential Workflow',channel='lifecycle',steps=[typed('Contracts/Compute',definition='logic',entry='initialize')]),
            'actA':typed('Contracts/Sequential Workflow Operation',channel='partyA',steps=[typed('Contracts/Compute',definition='logic',do=[call('act',side='A')])]),
            'actB':typed('Contracts/Sequential Workflow Operation',channel='partyB',steps=[typed('Contracts/Compute',definition='logic',do=[call('act',side='B')])]),
            'logic':typed('Contracts/Compute Definition',constants={'messageTypes':{
                'proposal':typed('MutualActivation/Change Proposal'),
                'decision':typed('MutualActivation/Change Decision',inResponseTo=typed('MutualActivation/Change Proposal')),
                'progress':typed('Agreements/Clause Progress'),
                'transition':typed('MutualActivation/Activation Decision Recorded'),
                'succeeded':typed('MutualActivation/Activation Succeeded'),
                'declined':typed('MutualActivation/Activation Declined')}},functions={
                    'revision':revision,'initialize':{'do':initial},'act':{'args':{'side':field('Text')},'do':common+[iff(eq(V('action'),k),v) for k,v in actions.items()]+tail}})}}

def make_agreement():
    verify=program_guard(['embedded','clauseProgress','applyClause','lifecycle','initialize'],['embedded','clauseProgress','applyClause','lifecycle','initialize'])+[need(eq(D('/activation/agreementId'),D('/agreementId')),'CLAUSE_AGREEMENT_MISMATCH'),
        need(eq(digest(D('/activation/partyA')),digest(D('/partyA'))),'CLAUSE_PARTY_A_MISMATCH'),
        need(eq(digest(D('/activation/partyB')),digest(D('/partyB'))),'CLAUSE_PARTY_B_MISMATCH'),
        need(eq(digest(D('/activation/type')),D('/activationType')),'CLAUSE_TYPE_MISMATCH'),
        need(eq(D('/activation/agreementType'),digest(D('/type'))),'AGREEMENT_TYPE_MISMATCH'),
        need(OR(eq(D('/activation/state/phase'),'NEGOTIATING'),eq(D('/activation/state/phase'),'CONSENTED'),eq(D('/activation/state/phase'),'DECLINED')),'INVALID_CLAUSE_PHASE')]
    synchronize=[*verify,let('priorPhase',D('/phase')),
        patch('/terms',D('/activation/state/settled'),'add'),
        patch('/phase',choose(eq(D('/activation/state/phase'),'CONSENTED'),'ACTIVE',D('/activation/state/phase')),'add'),
        iff(eq(D('/activation/state/phase'),'CONSENTED'),[
            need(NOT(D('/activation/state/pending')),'UNSETTLED_CONSENT'),
            need(AND(eq(D('/activation/state/signals/A'),'APPROVED'),eq(D('/activation/state/signals/B'),'APPROVED')),'TWO_APPROVALS_REQUIRED'),
            need(eq(D('/activation/state/consent/termsId'),D('/activation/state/targetId')),'CONSENT_TERMS_MISMATCH'),
            need(eq(D('/activation/state/consent/round'),D('/activation/state/round')),'CONSENT_ROUND_MISMATCH'),
            need(eq(digest(D('/activation/state/target')),digest(D('/activation/state/settled'))),'CONSENT_NOT_SETTLED'),
            patch('/acceptedRevision',D('/activation/state/consent'),'add'),
            iff(ne(V('priorPhase'),'ACTIVE'),[emit({'type':'Agreements/Agreement Activated','kind':'Agreement Activated','agreementId':D('/agreementId'),
                'termsId':D('/activation/state/targetId'),'round':D('/activation/state/round')})])]),
        iff(AND(eq(D('/activation/state/phase'),'DECLINED'),ne(V('priorPhase'),'DECLINED')),[emit({'type':'Agreements/Agreement Declined','kind':'Agreement Declined','agreementId':D('/agreementId'),'message':D('/activation/state/message')})]),
        emit({'type':'Agreements/Agreement Progressed','kind':'Agreement Progressed','agreementId':D('/agreementId'),'phase':choose(eq(D('/activation/state/phase'),'CONSENTED'),'ACTIVE',D('/activation/state/phase')),'round':D('/activation/state/round')})]
    return {'name':'Agreement','declaredContracts':['embedded','clauseProgress','applyClause','lifecycle','initialize'],'description':'Two-party Agreement root. Its designated embedded activation clause owns negotiation; the root owns ACTIVE.',
        'agreementId':field('Text'),'partyA':{'type':'Coordination/Actor','schema':{'required':True}},'partyB':{'type':'Coordination/Actor','schema':{'required':True}},
        'activation':field('Agreements/Clause'),
        'contracts':{
            'embedded':typed('Contracts/Process Embedded',paths=['/activation']),
            'clauseProgress':typed('Contracts/Embedded Node Channel',sourcePath='/activation',event={'type':'Agreements/Clause Progress'}),
            'applyClause':typed('Contracts/Sequential Workflow',channel='clauseProgress',steps=[typed('Contracts/Compute',do=synchronize)]),
            'lifecycle':typed('Contracts/Lifecycle Event Channel',event={'type':'Contracts/Document Processing Initiated'}),
            'initialize':typed('Contracts/Sequential Workflow',channel='lifecycle',steps=[typed('Contracts/Compute',do=verify[:-1]+[patch('/phase','NEGOTIATING','add'),patch('/acceptedRevision',{},'add'),patch('/terms',D('/activation/initialTerms'),'add')])])}}


def make_portfolio():
    event = lambda path: op('$event', '/event' + path)
    increment = lambda path: patch(path, op('$add', [D(path), 1]))
    observe = [
        need(op('$startsWith',[op('$event','/sourcePath'),'/agreements/']), 'NOT_A_SUBAGREEMENT'),
        increment('/observedEvents'),
        patch('/lastObserved',{'sourcePath':op('$event','/sourcePath'),'agreementId':event('/agreementId'),
                              'kind':event('/kind')}),
        iff(eq(event('/kind'),'Agreement Activated'),[
            increment('/activatedCount'),
            # A concrete portfolio policy: only selected suppliers get a follow-up.
            iff(op('$includes',{'list':D('/priorityAgreementIds'),'val':event('/agreementId')}),[
                increment('/followUpCount'),
                patch('/followUps',objset(D('/followUps'),event('/agreementId'),
                    {'status':'READY_FOR_ONBOARDING','termsId':event('/termsId')})),
                emit({'type':'AgreementExamples/Onboarding Requested','kind':'Onboarding Requested',
                      'agreementId':event('/agreementId'),'termsId':event('/termsId')})])]),
        iff(eq(event('/kind'),'Agreement Declined'),[increment('/declinedCount')])]
    return {'name':'Portfolio Agreement','type':'Agreements/Agreement',
        'declaredContracts':['embedded','clauseProgress','applyClause','lifecycle','initialize','subagreementEvents','observeSubagreements','initializePortfolio'],
        'description':'An Agreement with its own activation clause and a collection of independently managed Agreements.',
        'agreements':{},'priorityAgreementIds':[],'observedEvents':field('Integer'),'activatedCount':field('Integer'),'declinedCount':field('Integer'),
        'followUpCount':field('Integer'),'followUps':{},'lastObserved':{},
        'contracts':{
            'embedded':typed('Contracts/Process Embedded',paths=['/activation'],collectionPaths=['/agreements']),
            'subagreementEvents':typed('Contracts/Embedded Node Channel',event=typed('Agreements/Agreement Event')),
            'initializePortfolio':typed('Contracts/Sequential Workflow',channel='lifecycle',steps=[typed('Contracts/Compute',do=[patch('/'+key,0,'add') for key in ['observedEvents','activatedCount','declinedCount','followUpCount']])]),
            'observeSubagreements':typed('Contracts/Sequential Workflow',channel='subagreementEvents',
                                        steps=[typed('Contracts/Compute',do=observe)])}}


def write_package(folder, name, namespace, definitions, dependencies, readme):
    root=ROOT/folder
    (root/'types').mkdir(parents=True,exist_ok=True)
    (root/'README.md').write_text(readme+'\n')
    exports=[]
    for label,body in definitions.items():
        path='types/'+label.lower().replace(' ','-')+'.blue'
        (root/path).write_text(json.dumps(body,indent=2,ensure_ascii=False)+'\n')
        exports.append({'name':label,'path':path})
    imports={'Language':{'path':'../blue-language/dist/package.bluepkg'},
             'Contracts':{'path':'../blue-contracts/dist/package.bluepkg'},
             'Coordination':{'path':'../blue-coordination/dist/package.bluepkg'},**dependencies}
    cfg={'format':2,'name':name,'namespace':namespace,'version':'0.1.0-preview.2','previewOnly':True,
         'language':'Language','imports':imports,'executionRequires':[n for n in imports if n!='Language'],
         'exports':exports,'readme':'README.md','files':[]}
    (root/'blue-package.yaml').write_text(json.dumps(cfg,indent=2)+'\n')


def run():
    event=lambda name,parent,description: {'name':name,'type':parent,'description':description}
    agreements={
        'Clause':{'name':'Clause','description':'An embedded agreement clause with immutable participant context.',
                  'agreementId':field('Text'),'partyA':{'type':'Coordination/Actor','schema':{'required':True}},
                  'partyB':{'type':'Coordination/Actor','schema':{'required':True}}},
        'Clause Progress':event('Clause Progress','Coordination/Event','Notification only: the parent verifies completed child state.'),
        'Agreement Event':event('Agreement Event','Coordination/Event','A committed Agreement lifecycle observation.'),
        'Agreement Activated':event('Agreement Activated','Agreements/Agreement Event','The Agreement has installed the exact mutually approved settled revision.'),
        'Agreement Declined':event('Agreement Declined','Agreements/Agreement Event','Negotiation ended without activation.'),
        'Agreement Progressed':event('Agreement Progressed','Agreements/Agreement Event','The Agreement has consumed one committed clause update.'),
        'Agreement':make_agreement()}
    write_package('blue-agreements','blue-agreements','Agreements',agreements,{},
        '# Agreements\n\nReusable Agreement, Clause and typed lifecycle events. No dependency on a particular activation clause. '
        'Behaviour is ordinary Blue/Contracts/BEX data. Approved derived types may add declarations; instance-level executable overrides remain rejected.')
    activation={
        'Action':{'name':'Action','requestId':field('Text'),'action':field('Text'),'round':field('Integer'),'termsId':field('Text')},
        'Change Proposal':event('Change Proposal','Coordination/Request','Exact candidate, explanation, proposer and review context.'),
        'Change Decision':event('Change Decision','Coordination/Response','Correlated ACCEPTED, REJECTED, WITHDRAWN, SUPERSEDED or DECLINED decision.'),
        'Activation Event':event('Activation Event','Coordination/Event','Committed mutual-activation outcome or decision; never emitted for rejected actions or exact retries.'),
        'Activation Decision Recorded':event('Activation Decision Recorded','MutualActivation/Activation Event','A successful business action, with authenticated party, request ID and exact review context.'),
        'Activation Succeeded':event('Activation Succeeded','MutualActivation/Activation Event','Both principals approved settled terms. The parent still applies Agreement activation independently.'),
        'Activation Declined':event('Activation Declined','MutualActivation/Activation Event','A principal ended negotiation with a reason.'),
        'Mutual Activation Clause':make_clause()}
    write_package('clause-mutual-activation','clause-mutual-activation','MutualActivation',activation,
        {'Agreements':{'path':'../blue-agreements/dist/package.bluepkg'}},
        '# Mutual Activation\n\nTwo-party negotiation and mutual activation. READY is non-binding; accepting an edit is not approval. '
        'Definitions and event types only: dependencies are shared package pins, not copied runtime implementations. '
        'Use MutualActivation/Mutual Activation Clause and listen to MutualActivation/Activation Succeeded.')
    write_package('blue-agreement-examples','blue-agreement-examples','AgreementExamples',{
        'Onboarding Requested':event('Onboarding Requested','Coordination/Event','Portfolio follow-up for a selected activated subagreement.'),
        'Portfolio Agreement':make_portfolio()}, {'Agreements':{'path':'../blue-agreements/dist/package.bluepkg'}},
        '# Agreement examples\n\nThe portfolio has its own activation clause, observes typed events from every member of /agreements, '
        'counts activations and declines, and requests onboarding only for explicit priorityAgreementIds. '
        'Listeners run as Contracts workflows after genuine embedded-child delivery, never as host callbacks.')


if __name__=='__main__':run()
