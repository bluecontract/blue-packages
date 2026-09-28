"""Package validation plus explicitly scoped Contracts/BEX fixture tests."""
import unittest
from copy import deepcopy
from pathlib import Path
from support import Host,load,ROOT,SAFE,ACTIVATION,REMINDER,OPERATION_TIME,check_request
from blue_contracts import ContractError
from blue_packages.reader import PackageError,read_package

class FixtureTests(unittest.TestCase):
    def host(self,source=None,**kwargs):
        h=Host(source,**kwargs);self.addCleanup(h.close)
        result=h.initialize();self.assertTrue(result.commits,result.diagnostic)
        return h,result
    def success(self,result):self.assertTrue(result.commits,result.diagnostic)

    def test_01_initialization_without_timeline_entry_or_timestamp(self):
        h,result=self.host()
        self.assertEqual(len(h.pending),1);self.assertEqual(result.checkpoints,[])
        self.assertEqual(next(iter(h.pending.values()))['request']['timestamp'],ACTIVATION)
        self.assertEqual(h.business()['status'],'pending')
        self.assertFalse(any(row['kind']=='EXTERNAL' for row in result.work_trace))

    def test_02_whole_example_two_distinct_workflows(self):
        h,_=self.host();self.success(h.invoke());self.assertEqual(len(h.pending),2)
        h.progress(REMINDER,REMINDER);h.drain()
        self.assertEqual(h.business(),{'status':'pending','reminderCount':1,'lastReminder':'Check the reseller terms before activation.'})
        h.progress(ACTIVATION,ACTIVATION);h.drain()
        self.assertEqual(h.business()['status'],'active');self.assertEqual(h.business()['reminderCount'],1)
        self.assertEqual(len(h.pending),0)

    def test_03_activation_with_no_operation_ever(self):
        h,_=self.host();h.progress(ACTIVATION,ACTIVATION);h.drain()
        self.assertEqual(h.business(),{'status':'active','reminderCount':0,'lastReminder':''})

    def test_04_clock_progress_without_completeness_waits(self):
        h,_=self.host();h.progress(ACTIVATION)
        self.assertIsNone(h.fire_next());self.assertEqual(h.business()['status'],'pending')
        h.progress(ACTIVATION,ACTIVATION);self.assertIsNotNone(h.fire_next())

    def test_05_completeness_without_clock_progress_waits(self):
        h,_=self.host();h.progress(ACTIVATION-1,ACTIVATION)
        self.assertIsNone(h.fire_next());self.assertEqual(len(h.pending),1)

    def test_06_late_execution_keeps_requested_timestamp(self):
        h,_=self.host();h.progress(ACTIVATION+1000000,ACTIVATION+1000000);h.drain()
        row=h.firings[0];self.assertEqual(row['logicalTimestamp'],ACTIVATION)
        self.assertEqual(set(row['event']),{'type','registrationId','request'})
        self.assertEqual(row['event']['request']['timestamp'],ACTIVATION)

    def test_07_returned_request_is_unchanged(self):
        h,_=self.host();result=h.invoke();self.success(result)
        original=h.p.emitted(result)[0]
        h.progress(REMINDER,REMINDER);h.drain()
        self.assertEqual(h.firings[0]['requestBlueId'],result.public_events[0]['event'])
        self.assertEqual(h.firings[0]['event']['request'],original)
        self.assertEqual(h.identity(h.firings[0]['event']['request']),h.identity(original))

    def test_08_direct_bex_and_custom_step_emit_same_request(self):
        source=load();source['contracts']['scheduleReminder']['steps']=[load('direct-bex.blue')]
        a,_=self.host();b,_=self.host(source)
        ra=a.invoke();rb=b.invoke();self.success(ra);self.success(rb)
        self.assertEqual(a.p.emitted(ra),b.p.emitted(rb))
        self.assertEqual(ra.public_events[0]['event'],rb.public_events[0]['event'])

    def test_09_custom_step_rejects_explicit_type(self):
        source=load();step=source['contracts']['scheduleReminder']['steps'][-1]
        step['request']={'$objectSet':{'object':step['request'],'key':'type',
                         'val':{'$document':'/activationRequest/type'}}}
        h,_=self.host(source);before=h.state.identity
        result=h.invoke();self.assertFalse(result.commits)
        self.assertEqual(h.state.identity,before);self.assertEqual(len(h.pending),1)

    def test_10_custom_step_rejects_unknown_fields(self):
        source=load();source['contracts']['scheduleReminder']['steps'][-1]['request']['surprise']=1
        h,_=self.host(source);result=h.invoke();self.assertFalse(result.commits)
        self.assertFalse(result.public_events);self.assertEqual(len(h.pending),1)

    def test_11_check_then_schedule_is_explicit_failure(self):
        source=load();source['status']='active';h,_=self.host(source)
        result=h.invoke();self.assertFalse(result.commits);self.assertEqual(len(h.pending),1)

    def test_12_same_key_replaces_old_registration(self):
        h,_=self.host();self.success(h.invoke())
        first=next(rid for rid,row in h.pending.items() if row['request'].get('key')=='reminder')
        request=load('schedule-reminder.blue');request['request']['timestamp']=REMINDER+1000000;request['request']['message']='Replacement'
        self.success(h.invoke(request,OPERATION_TIME+1));self.assertNotIn(first,h.pending)
        self.assertEqual(h.terminal[first],'REPLACED');self.assertEqual(len(h.pending),2)
        h.progress(REMINDER,REMINDER);self.assertIsNone(h.fire_next())
        h.progress(REMINDER+1000000,REMINDER+1000000);h.drain()
        self.assertEqual(h.business()['lastReminder'],'Replacement')

    def test_13_cancel_reminder_does_not_cancel_activation(self):
        h,_=self.host();self.success(h.invoke());self.success(h.invoke(load('cancel-reminder.blue'),OPERATION_TIME+1))
        self.assertEqual([x['request']['key'] for x in h.pending.values()],['activation'])
        h.progress(ACTIVATION,ACTIVATION);h.drain()
        self.assertEqual(h.business()['status'],'active');self.assertEqual(h.business()['reminderCount'],0)

    def test_14_cancel_absent_key_is_noop(self):
        h,_=self.host();before=deepcopy(h.pending)
        self.success(h.invoke(load('cancel-reminder.blue')));self.assertEqual(before,h.pending)

    def test_15_exact_deadline_cancellation_precedes_timer(self):
        h,_=self.host();self.success(h.invoke())
        self.success(h.invoke(load('cancel-reminder.blue'),REMINDER))
        h.progress(REMINDER,REMINDER);self.assertIsNone(h.fire_next())
        self.assertEqual(h.business()['reminderCount'],0)

    def test_16_later_operation_cannot_overtake_pending_timer(self):
        h,_=self.host();self.success(h.invoke())
        with self.assertRaisesRegex(ContractError,'PENDING_TIMER_PRECEDES_INPUT'):
            h.invoke(load('cancel-reminder.blue'),REMINDER+1)
        self.assertEqual(len(h.pending),2)

    def test_17_backdated_new_schedule_is_rejected_before_fixture_commit(self):
        h,_=self.host();before=h.state.identity
        request=load('schedule-reminder.blue');request['request']['timestamp']=OPERATION_TIME-1
        with self.assertRaisesRegex(ContractError,'TIME_DEADLINE_BEFORE_POSITION'):h.invoke(request)
        self.assertEqual(h.state.identity,before);self.assertEqual(len(h.pending),1)

    def test_18_equal_operation_timestamp_may_arm_timer(self):
        h,_=self.host();request=load('schedule-reminder.blue');request['request']['timestamp']=OPERATION_TIME
        self.success(h.invoke(request));h.progress(OPERATION_TIME,OPERATION_TIME);h.drain()
        self.assertEqual(h.business()['reminderCount'],1)

    def test_19_initialization_is_not_repeated(self):
        h,_=self.host();before=deepcopy(h.pending);result=h.initialize()
        self.success(result);self.assertEqual(h.p.emitted(result),[]);self.assertEqual(before,h.pending)

    def test_20_replaying_same_committed_effect_is_idempotent(self):
        h,result=self.host();before=deepcopy(h.pending);h.commit(result)
        self.assertEqual(before,h.pending)

    def test_21_identical_unnamed_effects_are_distinct_occurrences(self):
        source=load();del source['activationRequest']['key']
        second=deepcopy(source['contracts']['initialize']['steps'][0]);second['name']='Register another activation'
        source['contracts']['initialize']['steps'].append(second)
        h,result=self.host(source)
        self.assertEqual(len(h.pending),2)
        events=h.p.emitted(result);self.assertEqual(events[0],events[1])
        self.assertEqual(len(set(h.pending)),2)
        expected=h.ordered();h.progress(ACTIVATION,ACTIVATION);h.drain()
        self.assertEqual([row['event']['registrationId'] for row in h.firings],expected)

    def test_22_scheduling_failure_rolls_back_document_and_requests(self):
        source=load();source['contracts']['scheduleReminder']['steps'].append({'type':'Contracts/Compute','do':[{'$fail':'Expected rollback'}]})
        h,_=self.host(source);before=h.state.identity;pending=deepcopy(h.pending)
        result=h.invoke();self.assertFalse(result.commits)
        self.assertFalse(result.public_events);self.assertEqual(before,h.state.identity);self.assertEqual(pending,h.pending)

    def test_23_shared_gas_failure_rolls_back(self):
        h,_=self.host();before=h.state.identity
        full=h.p.process(h.state,load('schedule-reminder.blue'),OPERATION_TIME);self.success(full)
        h.p.gas_limit=full.gas-1
        result=h.invoke();self.assertEqual(result.status,'GAS_LIMIT_EXCEEDED',result.diagnostic)
        self.assertFalse(result.public_events);self.assertEqual(h.state.identity,before);self.assertEqual(len(h.pending),1)

    def test_24_untrusted_timer_shape_does_not_fire(self):
        h,_=self.host();rid=h.ordered()[0];event,node,_=h.prepare_firing(rid);h.ticket=None
        result=h.p.process(h.state,event,ACTIVATION);self.success(result)
        self.assertEqual(h.p.read(result.snapshot,'/status'),'pending')
        self.assertEqual(len(h.pending),1)

    def test_25_mismatched_admission_is_rejected(self):
        h,_=self.host();h.progress(ACTIVATION,ACTIVATION);rid=h.ordered()[0]
        event,node,evidence=h.prepare_firing(rid);evidence[h.time_type]['fixtureTicket']='forged'
        result=h.deliver(node,ACTIVATION,evidence)
        self.assertFalse(result.commits);self.assertEqual(h.business()['status'],'pending')

    def test_26_completed_registration_cannot_fire_again(self):
        h,_=self.host();h.progress(ACTIVATION,ACTIVATION);rid=h.ordered()[0]
        event,node,evidence=h.prepare_firing(rid);old_ticket=deepcopy(h.ticket)
        h.fire_next();h.ticket=old_ticket
        result=h.deliver(node,ACTIVATION,evidence)
        self.assertFalse(result.commits);self.assertEqual(len(h.firings),1)

    def test_27_replaced_registration_cannot_admit_old_request(self):
        h,_=self.host();self.success(h.invoke())
        rid=next(rid for rid,row in h.pending.items() if row['request'].get('key')=='reminder')
        event,node,evidence=h.prepare_firing(rid);ticket=deepcopy(h.ticket);h.ticket=None
        replacement=load('schedule-reminder.blue');replacement['request']['message']='New registration'
        self.success(h.invoke(replacement,timestamp=OPERATION_TIME+1));h.progress(REMINDER,REMINDER);h.ticket=ticket
        result=h.deliver(node,REMINDER,evidence);self.assertFalse(result.commits)
        self.assertEqual(h.business()['reminderCount'],0)

    def test_28_custom_cancel_step_emits_same_cancellation(self):
        source=load();source['contracts']['cancelReminder']['steps']=[{'type':'Time/Cancel Timer','request':{'channel':'time','key':'reminder'}}]
        a,_=self.host();b,_=self.host(source)
        ra=a.invoke(load('cancel-reminder.blue'));rb=b.invoke(load('cancel-reminder.blue'))
        self.success(ra);self.success(rb);self.assertEqual(a.p.emitted(ra),b.p.emitted(rb))

    def test_29_request_schema_checks_numeric_timestamp(self):
        h,_=self.host();request=deepcopy(h.p.emitted(h.p.initialize(h.source))[0])
        for value in (-1,True,1.5,'2026-10-02T09:00:00Z',SAFE+1):
            invalid=deepcopy(request);invalid['timestamp']=value
            with self.subTest(value=value),self.assertRaises(Exception):h.p.blue.source(invalid)
        # This reader normalizes numeric source text (including Text-shaped
        # literals) under Integer. Require concrete integers at Time admission,
        # rather than silently changing the attached Language source parser.
        for value in (str(ACTIVATION),{'type':'Text','value':str(ACTIVATION)}):
            coerced=deepcopy(request);coerced['timestamp']=value
            with self.assertRaises(ContractError):check_request(coerced,typed=True)
            normalized=h.p.blue.project(h.p.blue.source(coerced))
            self.assertIs(type(normalized['timestamp']),int)
            self.assertEqual(normalized['timestamp'],ACTIVATION)
            check_request(normalized,typed=True)
        for value in (0,SAFE):
            valid=deepcopy(request);valid['timestamp']=value;h.p.blue.source(valid)

    def test_30_missing_timestamp_is_not_invented(self):
        h,_=self.host();request=deepcopy(next(iter(h.pending.values()))['request']);del request['timestamp']
        with self.assertRaises(Exception):h.p.blue.source(request)

    def test_31_native_runtime_refuses_unapproved_time_protocol(self):
        h,_=self.host()
        with self.assertRaisesRegex(PackageError,'unsupported executable protocol'):h.runtime.require(h.package)

    def test_32_mounted_package_does_not_install_runtime(self):
        h=Host(install=False);self.addCleanup(h.close)
        try:
            result=h.initialize()
        except ContractError:
            return
        self.assertFalse(result.commits)

    def test_33_archive_and_dependency_closure(self):
        h,_=self.host();package=read_package(ROOT/'dist/package.bluepkg')
        self.assertEqual(set(package.exports),{'Timer Channel','Timer Request','Timer Fired','Cancel Timer Request','Schedule Timer','Cancel Timer'})
        self.assertEqual(set(package.manifest['imports']),{'Language','BEX','Contracts','Coordination'})
        self.assertIn(package.manifest['protocol'],package.manifest['semanticSpecifications'])
        self.assertFalse(any('/src/' in path or path.startswith('vendor/') for path in package.files))

    def test_34_example_has_one_trigger_step_and_one_schedule_step(self):
        document=load();steps=[s for contract in document['contracts'].values() for s in contract.get('steps',[])]
        self.assertEqual(sum(s['type']=='Contracts/Trigger Event' for s in steps),1)
        self.assertEqual(sum(s['type']=='Time/Schedule Timer' for s in steps),1)
        self.assertIs(type(document['activationRequest']['timestamp']),int)

    def test_35_bex_observes_exact_original_request_identity(self):
        source=load()
        source['contracts']['recordReminderWhenDue']['steps'].append({
            'type':'Contracts/Compute','do':[{'$appendChange':{
                'op':'add','path':'/requestIdSeen','val':{'$nodeBlueId':{'$event':'/request'}}}}]})
        h,_=self.host(source);result=h.invoke();self.success(result)
        h.progress(REMINDER,REMINDER);h.drain()
        self.assertEqual(h.p.read(h.state,'/requestIdSeen'),result.public_events[0]['event'])

if __name__=='__main__':unittest.main()
