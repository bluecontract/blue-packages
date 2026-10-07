"""Uses only the verified package and the explicitly selected reference binding."""
from pathlib import Path
import json
from blue_language import Language
from blue_repository import Repository
from blue_contracts import Processor,export_snapshot,import_snapshot
from vendor import yaml
ROOT=Path(__file__).resolve().parents[1]
selected=json.loads((ROOT/'release.json').read_text())
manifest=json.loads((ROOT/'dist/package.json').read_text())
original=Repository((ROOT/'dist/repository.json').read_text())
repo=Repository.from_payload('consumer',{'contracts/'+e['name']:e['blueId'] for e in manifest['exports']},original.records)
blue=Language(repositories=[repo],core_contracts=False)
p=Processor(blue)
assert p.registry.specification==selected['specificationBlueId']
assert p.registry.types=={e['name']:e['blueId'] for e in manifest['exports']}
source=yaml.safe_load((ROOT/'examples/counter.blue').read_text())
event_source=yaml.safe_load((ROOT/'examples/request.blue').read_text())
# Resolve authoring aliases before transporting the event to independent workers.
event=json.loads(blue.create(json.dumps(event_source)).exact_text)
# Publish an exact source document through Language before processing.
authored=blue.create(json.dumps(source));blue.publish_document(authored)
state=p.create(source)
result=p.process(state,event,1)
assert result.status=='APPLIED',result.diagnostic
assert p.read(result.snapshot,'/count')==1
assert p.emitted(result)==[{'count':1}]
# Equivalent chunked execution, including real data transport to fresh workers.
a=p.begin(state,event,1)
while (token:=p.next_chunk(a)) is not None:
    worker=Processor()
    completion=worker.execute_chunk(json.loads(json.dumps(token.to_data())))
    p.accept_chunk(a,token,json.loads(json.dumps(completion.to_data())))
chunked=p.finish(a)
assert chunked.observations()==result.observations()
assert chunked.receipt==result.receipt
saved=export_snapshot(p,state)
cold=Processor()
restored=import_snapshot(cold,saved,state.identity)
replayed=cold.process(restored,event,1)
assert replayed.observations()==result.observations()
assert replayed.receipt==result.receipt
expected=json.loads((ROOT/'conformance/counter.json').read_text())['expected']
assert authored.blue_id==expected['authoredBlueId']
assert result.snapshot.documents[result.snapshot.root].blue_id==expected['resultBlueId']
assert result.gas==expected['gas'] and result.receipt==expected['receipt']
p.gas_limit=result.gas-1
failed=p.process(state,event,1)
assert failed.status=='GAS_LIMIT_EXCEEDED'
assert failed.snapshot.identity==state.identity and not failed.public_events
print(json.dumps({'packageBlueId':selected['packageBlueId'],'specificationBlueId':selected['specificationBlueId'],'authoredBlueId':authored.blue_id,'resultBlueId':result.snapshot.documents[result.snapshot.root].blue_id,'outcome':result.status,'count':1,'emitted':p.emitted(result),'gas':result.gas,'receipt':result.receipt,'chunkedEqualsDirect':True,'coldReplayEqualsDirect':True,'oneLessGasRollsBack':True},indent=2))
