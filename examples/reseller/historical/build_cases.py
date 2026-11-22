#!/usr/bin/env python3
"""Author native fixtures and independent expected outcomes; never execute business rules."""
from copy import deepcopy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
START = 1794661200000000
CUTOFF = 1794574800000000
GROUP = '/orders/o1/reservations/trip'
CATALOG = {
    'revision': 1, 'supplierId': 'seller', 'currency': 'USD',
    'entries': {
        'service': {'label': 'Boat service', 'description': 'Supplier-operated service',
                    'pricingUnit': 'per_unit', 'dateRequired': True, 'maxQuantity': 20,
                    'unitAmountMinor': 10000, 'guestDiscountPercent': 0,
                    'dateSelectionHint': 'Preferred date; availability requires supplier confirmation.'},
        'alternative': {'label': 'Alternative boat service', 'pricingUnit': 'per_unit',
                        'dateRequired': True, 'maxQuantity': 20, 'unitAmountMinor': 12000},
        'voucher': {'label': 'Undated voucher', 'pricingUnit': 'per_unit',
                    'dateRequired': False, 'maxQuantity': 20, 'unitAmountMinor': 5000},
    },
}


def operation(name, party, request, time=CUTOFF-100, **extra):
    return dict(operation=name, channel=party, request=request, timestampMicros=time, **extra)


def quote(lines=None, key='q1'):
    return operation('createQuote', 'partner', dict(key=key, catalogRevision=1, lines=lines or [
        dict(itemId='service', quantity=1, serviceDate='2026-11-14')]))


def place(groups=None, **extra):
    return operation('placeOrder', 'customer', dict(key='o1', quoteKey='q1', groups=groups or [
        dict(id='trip', lineIndices=[0], proposedStartMicros=START)], **extra),
        requireExactDocumentVersion=True,
        expect={GROUP+'/status': 'pending_supplier', GROUP+'/proposal/amountMinor': 10000})


def action(name, party, key, time=CUTOFF-1, group='trip', **request):
    return operation(name, party, dict(key=key, groupId=group, **request), time,
                     target='/orders/o1', requestFromState={
                         'expectedProposalBlueId': f'/orders/o1/reservations/{group}/proposalBlueId'})


def confirm(key='confirm-1', **kwargs):
    return action('confirmReservation', 'seller', key, **kwargs)


def cancel(time=CUTOFF+1, key='cancel-1', **kwargs):
    return action('cancelReservation', 'customer', key, time, reason='Changed plans', **kwargs)


def rejected(row, paths=None):
    return dict(row, status='FAILED', expectNoEffects=True,
                unchangedPaths=paths or ['/orders', '/orderIntents'])


def expected(row, **values):
    return dict(row, expect={GROUP+'/'+key: value for key, value in values.items()})


def scenario(name, coverage, steps, patch=None):
    return dict(name=name, requirements=coverage, sourcePatch={'/catalog': deepcopy(CATALOG), **(patch or {})},
                steps=steps)


def main():
    cases = []
    setup = lambda: [quote(), place()]
    for label, time, charge, released in [
            ('X01', CUTOFF-1, 0, 10000), ('X02', CUTOFF, 0, 10000),
            ('X03', CUTOFF+1, 10000, 0)]:
        cases.append(scenario(label+' inclusive microsecond cutoff', ['C01', label, 'F01', 'F03'],
            setup()+[confirm(), expected(cancel(time), status='cancelled', **{
                'decision/chargeMinor': charge, 'decision/releasedMinor': released,
                'decision/settlementStatus': 'payment_evidence_required'})]))
    cases.append(scenario('Pending withdrawal and cancel-before-confirm', ['X04', 'I07'],
        setup()+[expected(cancel(), status='cancelled', **{'decision/chargeMinor': 0}),
                 rejected(confirm(time=CUTOFF+2))]))
    cases.append(scenario('50 percent uses discounted accepted price', ['X05'],
        [quote(), dict(place(), expect={GROUP+'/proposal/amountMinor': 9500}), confirm(),
         expected(cancel(), **{'decision/chargeMinor': 4750, 'decision/releasedMinor': 4750})],
        {'/catalog/entries/service/guestDiscountPercent': 5,
         '/resellerTerms/cancellationPolicy/lateCancellationChargePercent': 50}))
    cases.append(scenario('Half-up rounds five minor units to three', ['X13'],
        [quote(), dict(place(), expect={GROUP+'/proposal/amountMinor': 5}), confirm(),
         expected(cancel(), **{'decision/chargeMinor': 3, 'decision/releasedMinor': 2})],
        {'/catalog/entries/service/unitAmountMinor': 5,
         '/resellerTerms/cancellationPolicy/lateCancellationChargePercent': 50}))
    cases.append(scenario('Supplier cancellation releases the whole price', ['X06'],
        setup()+[confirm(), expected(action('cancelBySupplier','seller','seller-cancel',CUTOFF+1,
            reason='Unsafe conditions'), **{'decision/chargeMinor': 0, 'decision/releasedMinor': 10000})]))
    cases.append(scenario('No-show requires supplier and reached confirmed start', ['X07','X08'],
        setup()+[rejected(action('reportNoShow','seller','no-show',START+1,reason='Absent')),
                 confirm(), rejected(action('reportNoShow','seller','no-show',START-1,reason='Absent')),
                 rejected(action('reportNoShow','customer','no-show',START+1,reason='Absent')),
                 expected(action('reportNoShow','seller','no-show',START+1,reason='Absent'),
                          status='no_show', **{'decision/chargeMinor': 10000})]))
    cases.append(scenario('Fulfilled service cannot be cancelled', ['X09'],
        setup()+[confirm(), rejected(action('fulfilGroup','seller','fulfil',START-1)),
                 action('fulfilGroup','seller','fulfil',START), rejected(cancel(START+1)),
                 rejected(action('cancelBySupplier','seller','supplier-cancel',START+1,reason='Too late'))]))
    cases.append(scenario('Ordinary cancellation after start rejects', ['X10'],
        setup()+[confirm(), rejected(cancel(START+1))]))
    cases.append(scenario('Client cannot supply time fee policy or actor', ['X11'], setup()+[confirm()]+[
        rejected(cancel(**{name: value})) for name,value in [
            ('nowMicros',CUTOFF-1),('chargeMinor',0),('policy',{}),('actor','seller')]]))
    cases.append(scenario('Zero-hour cutoff includes the exact start', ['X12'],
        setup()+[confirm(), expected(cancel(START), **{'decision/chargeMinor':0})],
        {'/resellerTerms/cancellationPolicy/freeCancellationHoursBeforeStart':0}))
    cases.append(scenario('Zero percent never creates a late charge', ['X12'],
        setup()+[confirm(), expected(cancel(), **{'decision/chargeMinor':0})],
        {'/resellerTerms/cancellationPolicy/lateCancellationChargePercent':0}))
    cases.append(scenario('Late confirmation requires explicit current consent', ['C06'],
        setup()+[expected(confirm(time=CUTOFF+1),status='pending_customer'),
                 rejected(action('acceptProposal','customer','accept-1',CUTOFF+2)),
                 expected(action('acceptProposal','customer','accept-1',CUTOFF+2,acceptImmediateCharge=True),
                          status='confirmed',confirmedStartMicros=START),
                 expected(cancel(CUTOFF+3),**{'decision/chargeMinor':10000})]))
    alternative = action('proposeAlternative','seller','alternative-1',CUTOFF-5,
        catalog=CATALOG,lines=[dict(itemId='alternative',quantity=1,serviceDate='2026-11-15')],
        proposedStartMicros=START+86400000000)
    stale = action('acceptProposal','customer','accept-stale',CUTOFF-3)
    stale.pop('requestFromState');stale['requestFromRemembered']={'expectedProposalBlueId':'firstProposal'}
    cases.append(scenario('Alternative quote waits for exact customer acceptance', ['C02','C03','I02'],
        [quote(),dict(place(),remember={'firstProposal':GROUP+'/proposalBlueId'}),
         expected(alternative,status='pending_customer',**{'proposal/amountMinor':12000}),rejected(stale),
         expected(action('acceptProposal','customer','accept-new',CUTOFF-2),status='confirmed',
                  confirmedStartMicros=START+86400000000),
         expected(cancel(CUTOFF+86400000001),**{'decision/chargeMinor':12000})]))
    cases.append(scenario('Partner has no supplier or customer authority', ['C04'],
        setup()+[rejected(action('confirmReservation','partner','forged-confirm')),
                 rejected(action('cancelReservation','partner','forged-cancel',reason='Forged')),
                 rejected(action('proposeAlternative','partner','forged-alternative',catalog=CATALOG,
                     lines=[dict(itemId='service',quantity=1,serviceDate='2026-11-14')],proposedStartMicros=START))]))
    cases.append(scenario('Undated products retain unknown start', ['C07','I09'],
        [quote([dict(itemId='voucher',quantity=1)]),
         dict(place([dict(id='trip',lineIndices=[0])]),expect={GROUP+'/status':'pending_supplier',
                                                          GROUP+'/proposal/amountMinor':5000}),
         rejected(confirm()),expected(cancel(),**{'decision/chargeMinor':0})]))
    cases.append(scenario('Past start cannot be confirmed', ['C09'],setup()+[rejected(confirm(time=START+1))]))
    cases.append(scenario('Explicit deadline prevents resurrection', ['C08'],setup()+[
        action('setResponseDeadline','seller','deadline-1',CUTOFF-10,deadlineMicros=CUTOFF),
        rejected(action('expireReservation','customer','expire-1',CUTOFF-1,reason='No answer')),
        rejected(confirm(time=CUTOFF)),
        expected(action('expireReservation','customer','expire-1',CUTOFF,reason='No answer'),status='expired'),
        rejected(confirm(time=CUTOFF+1))]))
    retry=cancel(CUTOFF+100)
    cases.append(scenario('Cold restore retry preserves one decision', ['I05','I06'],setup()+[
        confirm(),cancel(),dict(retry,restore=True,unchangedPaths=[GROUP,'/orders/o1/reservationRequests'],expectNoEffects=True),
        rejected(dict(retry,request=dict(retry['request'],reason='Different intention')))]))
    two_lines=[dict(itemId='service',quantity=1,serviceDate='2026-11-14'),
               dict(itemId='service',quantity=1,serviceDate='2026-11-15')]
    two_groups=[dict(id='trip',lineIndices=[0],proposedStartMicros=START),
                dict(id='other',lineIndices=[1],proposedStartMicros=START+86400000000)]
    cases.append(scenario('Two dates are independent fulfilment groups', ['I03'],
        [quote(two_lines),place(two_groups),confirm(),confirm(key='confirm-other',group='other'),
         dict(cancel(),unchangedPaths=['/orders/o1/reservations/other'],expect={
             GROUP+'/decision/basisMinor':10000,'/orders/o1/reservations/other/status':'confirmed'})]))
    for name,groups in [('overlap',[dict(id='trip',lineIndices=[0]),dict(id='other',lineIndices=[0,1])]),
                        ('ungrouped',[dict(id='trip',lineIndices=[0])]),
                        ('mixed dates',[dict(id='trip',lineIndices=[0,1])])]:
        bad=place(groups);bad.pop('expect')
        cases.append(scenario('Invalid group partition '+name,['I04'],[quote(two_lines),rejected(bad)]))
    foreign=deepcopy(CATALOG);foreign['supplierId']='foreign-seller'
    bad=place();bad.pop('expect')
    cases.append(scenario('Foreign seller quote cannot become this order',['I04'],[quote(),rejected(bad)],{'/catalog':foreign}))
    for mode in ['without readiness','with readiness','late without consent','late accepted']:
        groups=[dict(id='trip',lineIndices=[0],proposedStartMicros=START)]
        steps=[quote()]
        if mode!='without readiness':
            steps.append(operation('approveAvailability','seller',dict(quoteKey='q1',groups=groups,
                reference='Explicit supplier fixture, not live inventory')))
        p=place(groups,acceptImmediateCharge=mode=='late accepted');p.pop('expect')
        if mode.startswith('late'):p['timestampMicros']=CUTOFF+1
        if mode in ['without readiness','late without consent']:steps.append(rejected(p))
        else:steps.append(expected(p,status='confirmed',confirmedStartMicros=START))
        cases.append(scenario('Automatic '+mode,['C05','C06'],steps,
            {'/resellerTerms/confirmationMode':'automatic'}))
    for path,value in [('freeCancellationHoursBeforeStart',-1),('freeCancellationHoursBeforeStart',8761),
                       ('lateCancellationChargePercent',-1),('lateCancellationChargePercent',101)]:
        bad=place();bad.pop('expect')
        cases.append(scenario('Reject invalid policy '+path+' '+str(value),[],[quote(),rejected(bad)],
            {'/resellerTerms/cancellationPolicy/'+path:value}))
    result={'format':'blue-native-reseller-scenarios/1','scenarios':cases}
    (HERE/'reservation.case.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f'Authored {len(cases)} native scenarios; expected monetary values are explicit fixtures.')


if __name__=='__main__':
    main()
