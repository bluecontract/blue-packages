"""Author two data-only candidates. Helpers assemble BEX; they never execute it.
Run build_reseller_packages.py to publish in exact dependency order.
"""
from pathlib import Path
import json
from copy import deepcopy
from author_mutual_activation import (
    op,V,D,C,eq,ne,AND,OR,NOT,kind,has,get,choose,objset,let,iff,need,call,ret,
    digest,emit,patch,typed,field,program_guard,make_agreement,
)
ROOT=Path(__file__).resolve().parents[1]


def write_package(folder,namespace,definitions,dependencies,readme,files=()):
    root=ROOT/folder
    (root/'types').mkdir(parents=True,exist_ok=True)
    exports=[]
    for label,definition in definitions.items():
        relative='types/'+label.lower().replace(' ','-')+'.blue'
        (root/relative).write_text(json.dumps(definition,indent=2,ensure_ascii=False)+'\n')
        exports.append({'name':label,'path':relative})
    (root/'README.md').write_text(readme.strip()+'\n')
    imports={prefix:{'path':'../'+name+'/dist/package.bluepkg'} for prefix,name in [
        ('Language','blue-language'),('Contracts','blue-contracts'),
        ('Coordination','blue-coordination'),('Agreements','blue-agreements'),*dependencies]}
    cfg={'format':2,'name':folder,'namespace':namespace,'version':'0.1.0-preview.1',
         'previewOnly':True,'language':'Language','imports':imports,
         'executionRequires':[prefix for prefix in imports if prefix!='Language'],
         'exports':exports,'readme':'README.md','files':list(files)}
    (root/'blue-package.yaml').write_text(json.dumps(cfg,indent=2)+'\n')


def immediate_termination():
    names=['partyA','partyB','lifecycle','initialize','terminateA','terminateB','logic']
    guard=program_guard(names,names)
    context=[
        need(kind(D('/agreementId'),'text'),'AGREEMENT_ID_REQUIRED'),
        need(ne(D('/agreementId'),''),'AGREEMENT_ID_REQUIRED'),
        need(ne(digest(D('/partyA')),digest(D('/partyB'))),'TWO_DISTINCT_PARTIES_REQUIRED'),
        need(eq(digest(D('/contracts/partyA/actor')),digest(D('/partyA'))),'PARTY_A_CHANNEL_MISMATCH'),
        need(eq(digest(D('/contracts/partyB/actor')),digest(D('/partyB'))),'PARTY_B_CHANNEL_MISMATCH'),
        need(op('$includes',{'list':['A','B','EITHER'],'val':D('/allowedParty')}),'INVALID_TERMINATION_PARTY'),
        need(kind(D('/termsId'),'text'),'ACCEPTED_TERMS_ID_REQUIRED'),
        need(ne(D('/termsId'),''),'ACCEPTED_TERMS_ID_REQUIRED'),
        need(kind(D('/round'),'integer'),'ACCEPTED_ROUND_REQUIRED'),
        need(op('$gt',[D('/round'),0]),'ACCEPTED_ROUND_REQUIRED'),
    ]
    initialize=[*guard,*context,patch('/state',{'phase':'OPEN','termination':{}},'add')]
    terminate=[
        *guard,*context,
        let('req',op('$binding','call/request')),
        need(kind(V('req'),'object'),'REQUEST_REQUIRED'),
        need(kind(V('req','/requestId'),'text'),'REQUEST_ID_REQUIRED'),
        need(ne(V('req','/requestId'),''),'REQUEST_ID_REQUIRED'),
        need(op('$isEmpty',op('$filter',{'in':op('$keys',V('req')),'item':'key',
            'where':NOT(op('$includes',{'list':['requestId','termsId','reason'],'val':V('key')}))})),
             'UNKNOWN_TERMINATION_REQUEST_FIELD'),
        need(OR(NOT(has(V('req'),'reason')),kind(V('req','/reason'),'text')),'REASON_MUST_BE_TEXT'),
        need(eq(V('req','/termsId'),D('/termsId')),'STALE_TERMS'),
        need(OR(eq(D('/allowedParty'),'EITHER'),eq(D('/allowedParty'),V('side'))),'TERMINATION_NOT_PERMITTED'),
        let('requestHash',digest(V('req'))),
        iff(eq(D('/state/phase'),'TERMINATED'),[
            need(AND(eq(D('/state/termination/party'),V('side')),
                     eq(D('/state/termination/requestId'),V('req','/requestId'))),'TERMINATION_CLOSED'),
            need(eq(D('/state/termination/requestHash'),V('requestHash')),'REQUEST_ID_REUSE'),ret(True)]),
        need(eq(D('/state/phase'),'OPEN'),'TERMINATION_CLOSED'),
        let('record',{'agreementId':D('/agreementId'),'party':V('side'),
            'actor':choose(eq(V('side'),'A'),D('/partyA'),D('/partyB')),
            'requestId':V('req','/requestId'),'requestHash':V('requestHash'),
            'termsId':D('/termsId'),'round':D('/round'),'allowedParty':D('/allowedParty'),
            'reason':op('$default',[V('req','/reason'),'']),
            'timestampUs':op('$binding','timestamp'),
            'eventId':digest(op('$binding','processingEvent'))}),
        patch('/state',{'phase':'TERMINATED','termination':V('record')}),
        emit(objset(V('record'),'type',C('noticeType','/type'))),
    ]
    clause={'name':'Immediate Termination Clause','type':'Agreements/Clause',
        'description':'An active agreement installs this child from exact mutually approved terms. A permitted principal can terminate immediately without counterparty approval. The parent verifies and commits the agreement outcome.',
        'declaredContracts':names,'allowedParty':{'type':'Text','schema':{'enum':['A','B','EITHER']}},
        'termsId':field('Text'),'round':field('Integer'),
        'contracts':{
            'partyA':typed('Coordination/Timeline Channel'),'partyB':typed('Coordination/Timeline Channel'),
            'lifecycle':typed('Contracts/Lifecycle Event Channel',event=typed('Contracts/Document Processing Initiated')),
            'initialize':typed('Contracts/Sequential Workflow',channel='lifecycle',steps=[typed('Contracts/Compute',definition='logic',entry='initialize')]),
            'terminateA':typed('Contracts/Sequential Workflow Operation',channel='partyA',steps=[typed('Contracts/Compute',definition='logic',do=[call('terminate',side='A')])]),
            'terminateB':typed('Contracts/Sequential Workflow Operation',channel='partyB',steps=[typed('Contracts/Compute',definition='logic',do=[call('terminate',side='B')])]),
            'logic':typed('Contracts/Compute Definition',constants={'noticeType':typed('ImmediateTermination/Termination Exercised')},
                functions={'initialize':{'do':initialize},'terminate':{'args':{'side':field('Text')},'do':terminate}})}}
    return {
        'Immediate Termination Terms':{'name':'Immediate Termination Terms',
            'description':'Passive, negotiable configuration. A means first party; B means second party; EITHER means either party acting alone. Effective only after mutual activation of the containing agreement.',
            'allowedParty':{'type':'Text','schema':{'enum':['A','B','EITHER'],'required':True}}},
        'Termination Exercised':{'name':'Termination Exercised','type':'Agreements/Clause Progress',
            'description':'A genuine completed child reports exercise of the agreed termination right. The agreement root verifies child state before committing termination.'},
        'Agreement Terminated':{'name':'Agreement Terminated','type':'Agreements/Agreement Event',
            'description':'The agreement root committed termination of its accepted revision. Not a request for counterparty consent.'},
        'Immediate Termination Clause':clause,
    }

TERMINATION_README='''
# Immediate Termination

Independent data-only Blue package, namespace `ImmediateTermination`.

`Immediate Termination Terms` is the negotiable clause configuration:

```yaml
type: ImmediateTermination/Immediate Termination Terms
allowedParty: A
```

`A` means the first party, `B` the second party, and `EITHER` means either one
acting alone. `EITHER` does not require both signatures. The parameter has no
silent default. The clause provides termination without a cause, notice period,
or counterparty acceptance; an optional reason is retained as evidence only.

`Immediate Termination Clause` is the executable embedded instance. A containing
agreement installs it only after approval, with the approved option, accepted
terms ID / round, both party actors and authenticated Timeline channels. This
separation keeps negotiating a clause from executing it. Do not independently
install a child and treat its event as proof that an unrelated agreement ended.

Call `terminateA` on channel `partyA`, or `terminateB` on channel `partyB`, with
`request: {requestId: ..., termsId: ..., reason: ...}`. The receiver is the
embedded clause's document, not the agreement's activation clause. The actor is
determined by the authenticated channel, never by a caller-supplied party field.
The current `Runtime.agreements()` profile supplies Coordination authentication;
plain Contracts processing is not an authentication boundary.

A permitted first call changes the child from OPEN to TERMINATED and emits
`Termination Exercised`. The parent must check the genuine embedded source,
completed state, exact clause type, approved policy, actors, channels and revision;
only then may it emit `Agreement Terminated` and change its phase. The reseller
package contains that composition. Events forged on an external Timeline are not
embedded completions. Exact request retries have no additional business effect;
reuse of the same request ID with altered content and subsequent fresh termination
requests are rejected. Business termination does not use `Terminate Processing`:
state and evidence remain readable, and exact retries remain recognizable.

There is no native termination plugin, package-specific Python/Java SDK, copied
foundation source, environment, credential or install hook. The dependency pins
are in `blue-package.lock.json`; the data-only publication is `dist/package.bluepkg`.
'''

TEXT_CLAUSES={
 'appointment':('1. Appointment and relationship',
    'Party A is the Supplier and Party B is the Reseller. Upon activation, the Supplier appoints the Reseller on a non-exclusive basis to market and resell the Products within the Territory. The Reseller acts in its own name and for its own account, is not an agent of the Supplier, and cannot bind the Supplier or make commitments on its behalf.'),
 'productsAndTerritory':('2. Products and territory',
    'Products and Territory are those recorded in the commercial schedule. No exclusivity, minimum purchase volume, protected customer list or right outside that scope is granted unless expressly added to the agreed terms. Material changes to the Products or Territory require a separately agreed amendment; this template automates pre-activation negotiation only.'),
 'ordersAndFulfilment':('3. Orders and fulfilment',
    'Each purchase requires a separate order accepted by the Supplier. A quotation or customer commitment made by the Reseller does not itself oblige the Supplier to accept an order. Accepted orders specify quantities, delivery, applicable charges and any support obligations. This agreement does not automatically create, accept, cancel or fulfil orders.'),
 'pricingAndPayment':('4. Wholesale price and payment',
    'The Reseller discount in the commercial schedule applies to the Supplier list price specified in each accepted order. Taxes, delivery costs and other charges must be stated in that order. Payment is due within the scheduled payment term from the invoice date unless that order states otherwise. The Reseller determines its own resale prices. This document records commercial terms but does not initiate payments.'),
 'marketingAndMarks':('5. Marketing and intellectual property',
    'During the active term, the Reseller may use Supplier-approved product descriptions and marks solely to market the Products within the agreed scope. The Supplier retains ownership of its intellectual property. The Reseller must not claim to be the Supplier, alter product claims without approval, or grant rights it does not hold. Permission to use the marks for new marketing ends on termination.'),
 'customerResponsibilities':('6. Customer responsibilities',
    'The Reseller is responsible for its own customer offers, resale terms and communications. Each party is responsible for the personnel and services it expressly undertakes to provide. Product warranties, returns, service levels and support commitments must be stated in the relevant order or another expressly accepted document; they are not inferred from activation of this agreement.'),
 'confidentiality':('7. Confidentiality and customer information',
    'Each party will protect the other party confidential information, use it only for this relationship, and disclose it only to people who need it for that purpose and are bound to protect it. This excludes information already lawfully known, independently developed, public without breach, or lawfully obtained from another source. Any required disclosure is limited to what is required. The confidentiality period after termination is specified in the commercial schedule. Neither party may share personal customer information merely because this agreement is active.'),
 'authorityAndCompliance':('8. Authority and compliance',
    'Each party remains responsible for the authority of people or agents acting for it and for the requirements applicable to its own activities. Participation by an agent does not by itself authorize it to approve terms, place orders or terminate. This demonstration submits actions directly from the two principal actors; delegated authority, when used, requires a separately verified Mandate.'),
 'activation':('9. Negotiation and mutual activation',
    'This agreement is not active while it is being negotiated. Accepting a proposed edit and marking READY are not activation approval. Both principals must approve the same settled terms and review round through the Mutual Activation Clause. Changes to the reviewed candidate invalidate prior-round signals. The accepted revision and both approval records are retained when the agreement becomes ACTIVE.'),
 'terminationEffects':('10. End of the relationship',
    'When the optional Immediate Termination Terms clause is present in the accepted revision, the specified party, or either party if EITHER is selected, may terminate this agreement immediately through the executable clause without a second approval or a notice period. No cause is required; an optional reason is recorded. If the clause is absent, this template provides no immediate-termination operation. Termination takes effect in the recorded business state when the agreement commits TERMINATED after processing the authorized notice. It ends authorization for new activity under this agreement but does not automatically cancel previously accepted orders, discharge accrued payment obligations, refund money or terminate other Blue documents. Confidentiality and obligations expressly stated to survive continue as written.'),
 'noticesAndRecords':('11. Notices and records',
    'The agreed principal actors and Timeline channels identify who submits automated actions. The agreement records exact terms, approval evidence and termination evidence. A termination event is a recorded outcome, not a request that the counterparty must accept. A notice outside those configured operations has no automatic state-changing effect in this template.'),
 'completeTermsAndDisputes':('12. Complete terms and unresolved matters',
    'The commercial schedule and numbered clauses together form the proposed relationship terms. Operational changes after activation require another expressly agreed instrument; no post-activation amendment workflow is implemented here. The parties will first attempt to resolve disputes through their named business contacts. This demonstration intentionally makes no governing-law, venue, statutory-remedy or enforceability determination; those matters and any sector-specific requirements must be settled before real use.'),
}


def make_reseller(termination_ids,activation_id):
    default_terms={
        'title':'Non-exclusive Reseller Agreement',
        'commercial':{'supplierName':'Example Supplier','resellerName':'Example Reseller',
            'products':'Supplier standard products identified in accepted orders',
            'territory':'Spain','currency':'EUR','resellerDiscountBps':1500,
            'paymentTermDays':30,'confidentialitySurvivalMonths':24,
            'supplierContact':'Supplier commercial contact','resellerContact':'Reseller commercial contact'},
        'clauses':{key:{'heading':heading,'text':text} for key,(heading,text) in TEXT_CLAUSES.items()}}
    default_terms['clauses']['immediateTermination']={
        'type':'ImmediateTermination/Immediate Termination Terms','allowedParty':'EITHER'}
    base=make_agreement();contracts=deepcopy(base['contracts'])
    contracts['embedded']=typed('Contracts/Process Embedded',paths=['/activation'],collectionPaths=['/clauses'])
    contracts['guardActivation']=typed('Contracts/Sequential Workflow',channel='clauseProgress',order=-1,
        steps=[typed('Contracts/Compute',do=[need(ne(D('/phase'),'TERMINATED'),'AGREEMENT_TERMINATED')])])
    contracts['initialize']['steps'][0]['do'].extend([
        need(eq(digest(D('/activation/type')),D('/type/activationType')),'UNSUPPORTED_ACTIVATION_CLAUSE_TYPE'),
        need(kind(D('/activation/initialTerms/clauses'),'object'),'INITIAL_TERMS_CLAUSES_REQUIRED'),
        need(op('$isEmpty',op('$keys',D('/clauses'))),'RUNTIME_CLAUSES_MUST_START_EMPTY'),
        patch('/termination',{},'add')])
    config=D('/activation/state/settled/clauses/immediateTermination')
    validate=[
        need(kind(config,'object'),'INVALID_TERMINATION_TERMS'),
        need(eq(digest(D('/activation/state/settled/clauses/immediateTermination/type')),
                D('/type/terminationTermsType')),'UNSUPPORTED_TERMINATION_TERMS_TYPE'),
        need(op('$isEmpty',op('$filter',{'in':op('$keys',config),'item':'key',
            'where':NOT(op('$includes',{'list':['type','name','description','allowedParty'],'val':V('key')}))})),
             'UNSUPPORTED_TERMINATION_TERMS_FIELD'),
        need(op('$includes',{'list':['A','B','EITHER'],
                            'val':D('/activation/state/settled/clauses/immediateTermination/allowedParty')}),
             'INVALID_TERMINATION_PARTY')]
    instance=objset({
        'agreementId':D('/agreementId'),'agreementType':digest(D('/type')),
        'partyA':D('/partyA'),'partyB':D('/partyB'),
        'allowedParty':D('/activation/state/settled/clauses/immediateTermination/allowedParty'),
        'termsId':D('/activation/state/targetId'),'round':D('/activation/state/round'),
        'contracts':{'partyA':D('/activation/contracts/partyA'),'partyB':D('/activation/contracts/partyB')},
    },'type',objset({},'blueId',D('/type/terminationClauseType')))
    contracts['applyClause']['steps'][0]['do'].extend([
        need(eq(digest(D('/activation/type')),D('/type/activationType')),'UNSUPPORTED_ACTIVATION_CLAUSE_TYPE'),
        iff(AND(eq(D('/activation/state/phase'),'CONSENTED'),
                has(D('/activation/state/settled/clauses'),'immediateTermination')),[
            *validate,iff(NOT(has(D('/clauses'),'immediateTermination')),[
                patch('/clauses/immediateTermination',instance,'add')])])])
    record=D('/clauses/immediateTermination/state/termination')
    verify=[
        *program_guard([],[]),
        need(eq(op('$event','/sourcePath'),'/clauses/immediateTermination'),'INVALID_TERMINATION_SOURCE'),
        need(eq(digest(D('/clauses/immediateTermination/type')),D('/type/terminationClauseType')),'UNSUPPORTED_TERMINATION_CLAUSE_TYPE'),
        need(eq(D('/clauses/immediateTermination/agreementId'),D('/agreementId')),'CLAUSE_AGREEMENT_MISMATCH'),
        need(eq(D('/clauses/immediateTermination/agreementType'),digest(D('/type'))),'AGREEMENT_TYPE_MISMATCH'),
        need(eq(digest(D('/clauses/immediateTermination/partyA')),digest(D('/partyA'))),'CLAUSE_PARTY_A_MISMATCH'),
        need(eq(digest(D('/clauses/immediateTermination/partyB')),digest(D('/partyB'))),'CLAUSE_PARTY_B_MISMATCH'),
        need(eq(digest(D('/clauses/immediateTermination/contracts/partyA')),digest(D('/activation/contracts/partyA'))),'TERMINATION_CHANNEL_A_MISMATCH'),
        need(eq(digest(D('/clauses/immediateTermination/contracts/partyB')),digest(D('/activation/contracts/partyB'))),'TERMINATION_CHANNEL_B_MISMATCH'),
        need(eq(D('/clauses/immediateTermination/allowedParty'),D('/terms/clauses/immediateTermination/allowedParty')),'TERMINATION_POLICY_MISMATCH'),
        need(eq(D('/clauses/immediateTermination/termsId'),D('/acceptedRevision/termsId')),'TERMINATION_REVISION_MISMATCH'),
        need(eq(D('/clauses/immediateTermination/round'),D('/acceptedRevision/round')),'TERMINATION_ROUND_MISMATCH'),
        need(eq(D('/clauses/immediateTermination/state/phase'),'TERMINATED'),'TERMINATION_NOT_COMPLETED'),
        need(eq(op('$event','/event/requestId'),get(record,'requestId')),'TERMINATION_NOTICE_MISMATCH'),
        need(eq(op('$event','/event/termsId'),D('/acceptedRevision/termsId')),'TERMINATION_NOTICE_MISMATCH'),
        need(eq(get(record,'termsId'),D('/acceptedRevision/termsId')),'TERMINATION_REVISION_MISMATCH'),
        need(eq(get(record,'round'),D('/acceptedRevision/round')),'TERMINATION_ROUND_MISMATCH'),
        need(OR(eq(D('/terms/clauses/immediateTermination/allowedParty'),'EITHER'),
                eq(D('/terms/clauses/immediateTermination/allowedParty'),get(record,'party'))),'TERMINATION_NOT_PERMITTED'),
        iff(eq(D('/phase'),'TERMINATED'),[
            need(eq(digest(D('/termination')),digest(record)),'CONFLICTING_TERMINATION'),ret(True)]),
        need(eq(D('/phase'),'ACTIVE'),'AGREEMENT_NOT_ACTIVE'),
        patch('/phase','TERMINATED'),patch('/termination',record),
        emit(objset(objset(record,'kind','Agreement Terminated'),'type',C('terminatedType','/type')))]
    contracts['terminationProgress']=typed('Contracts/Embedded Node Channel',sourcePath='/clauses/immediateTermination',
                                         event=typed('ImmediateTermination/Termination Exercised'))
    contracts['applyTermination']=typed('Contracts/Sequential Workflow',channel='terminationProgress',
        steps=[typed('Contracts/Compute',constants={'terminatedType':typed('ImmediateTermination/Agreement Terminated')},do=verify)])
    return {'name':'Reseller Agreement','type':'Agreements/Agreement',
        'description':'Complete non-exclusive supplier/reseller template. A is Supplier; B is Reseller. Reuses exact mutual activation and immediate termination packages without native business code.',
        'declaredContracts':list(contracts),'activationType':activation_id,
        'terminationTermsType':termination_ids['Immediate Termination Terms'],
        'terminationClauseType':termination_ids['Immediate Termination Clause'],
        'defaultTerms':default_terms,
        'activation':{'type':'MutualActivation/Mutual Activation Clause'},
        'clauses':{},'termination':{},'contracts':contracts}

RESELLER_README='''
# Reseller Agreement

A data-only `Reseller/Reseller Agreement` derived from `Agreements/Agreement`.
Party A is the Supplier; party B is the Reseller. The type includes the full
commercial schedule and twelve readable clauses. It explicitly imports and uses
`MutualActivation/Mutual Activation Clause` and the independent
`ImmediateTermination` package. The original Agreements and Mutual Activation
publications are neither edited nor republished.

Read `docs/agreement-content.md` for the complete proposed business wording.
These are demonstration terms, not a jurisdiction-qualified legal instrument.
Prices, products, territory, contacts, authority and legal requirements need to
be completed/reviewed before real transactions. Text-only obligations are not
silently represented as automated fulfilment, payment or enforcement.

## Composition

* Copy the type's `/defaultTerms` into a plain proposed terms object, edit it, and
  supply it as `/activation/initialTerms`. Defaults are not inherited into the
  negotiated terms: an omitted optional clause must actually stay absent.
* `/activation` is the managed Mutual Activation Clause. Bind both principal actors, their
  Timeline channels, `agreementId`, and `agreementType` when constructing it.
* Negotiable content lives in `/activation/state/target` and `settled`; the root
  mirrors settled terms at `/terms`. A proposed clause remains passive data.
* The optional `/terms/clauses/immediateTermination` is a typed
  `ImmediateTermination/Immediate Termination Terms` value, parameterized by
  `allowedParty: A | B | EITHER`. The published template includes EITHER; authors
  may choose A/B at creation or remove the option before initialization and
  negotiate its addition. The demo takes the latter route.
* Only mutual consent to settled terms activates the agreement and installs the
  executable `/clauses/immediateTermination` child from the exact approved
  parameter, revision and authenticated channels. An absent clause installs
  nothing. Caller-supplied contracts in negotiated data are not executed.
* Invoke `terminateA`/`terminateB` on that child's `partyA`/`partyB` channel. The
  permitted principal acts alone. The root verifies the completed child before
  changing ACTIVE to TERMINATED and emitting Agreement Terminated.

The lifecycle is NEGOTIATING -> ACTIVE -> TERMINATED, with DECLINED as the other
negotiation outcome. Termination cannot re-open negotiation, reactivate the
agreement, rewrite accepted terms or automatically cancel unrelated orders.
No extra `terminateProcessing` action, counterparty approval or timer is needed.

The template has concrete, immutable lifecycle glue in its derived Blue type;
it does not assume that adding a name to a clauses list installs executable
behaviour. The extension specifically recognizes this known termination type.
It is not a generic loader for arbitrary negotiated programs.

The exact runtime profile and Coordination requirements must be supported as
well as the business archives. Mount aliases explicitly: importing Reseller does
not implicitly expose the ImmediateTermination or MutualActivation namespaces.
Use the provided integration scenario and Codex prompt for the signed-Timeline
story and the browser lesson. No package-specific SDK is required.
'''


def author_termination():
    write_package('clause-immediate-termination','ImmediateTermination',immediate_termination(),[],TERMINATION_README)


def author_reseller(termination_ids,activation_id):
    definition=make_reseller(termination_ids,activation_id)
    root=ROOT/'agreement-reseller';(root/'docs').mkdir(parents=True,exist_ok=True)
    terms=definition['defaultTerms']
    text=['# Non-exclusive Reseller Agreement','',
          '> Demonstration business terms. A is Supplier; B is Reseller. Not qualified for legal use in any jurisdiction.','',
          '## Commercial schedule','']
    for k,v in terms['commercial'].items():text.append(f'- **{k}:** {v}')
    text+=['','Discount is in basis points: 1500 means 15%. Payment terms are in calendar days.','']
    for _,(heading,body) in TEXT_CLAUSES.items():text.extend(['## '+heading,'',body,''])
    text.extend(['## Optional immediate-termination configuration','',
                 '`type: ImmediateTermination/Immediate Termination Terms` with `allowedParty: A`, `B`, or `EITHER`.',
                 'The published default is EITHER. The integration scenario negotiates addition of the clause with A only.',''])
    (root/'docs/agreement-content.md').write_text('\n'.join(text))
    write_package('agreement-reseller','Reseller',{'Reseller Agreement':definition},[
        ('MutualActivation','clause-mutual-activation'),('ImmediateTermination','clause-immediate-termination')],
        RESELLER_README,files=['docs/agreement-content.md'])

if __name__=='__main__':
    raise SystemExit('Use tools/build_reseller_packages.py to author and build in dependency order.')
