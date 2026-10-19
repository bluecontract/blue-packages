from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import bootstrap
from release import checked_package
from blue_bex import Engine, Context, Gas
from blue_language import Language
from blue_contracts.reference.language import Bridge
p=checked_package()
context=Context(matcher=Bridge(Language(core_contracts=False)).matches)
result=Engine().execute(json.loads((ROOT/'examples/program.json').read_text()),context,gas=Gas(100000))
assert result.value==15000
print(json.dumps({'packageBlueId':p.manifest['packageBlueId'],'value':result.value,'gas':result.gas_used,'events':result.events,'changeset':result.changeset},indent=2))
