from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'tools'))
from verify_runtime import verify_current_runtime
verify_current_runtime()
import json
from blue_bex import Engine, Context, Gas
from blue_language import Language
from blue_contracts.reference.language import Bridge
from blue_packages import PackageStore
p=PackageStore(ROOT.parent).package('blue-bex')
context=Context(matcher=Bridge(Language(core_contracts=False)).matches)
result=Engine().execute(json.loads((ROOT/'examples/program.json').read_text()),context,gas=Gas())
assert result.value==15000
print(json.dumps({'packageBlueId':p.blue_id,'value':result.value,'gas':result.gas_used,'events':result.events,'changeset':result.changeset},indent=2))
