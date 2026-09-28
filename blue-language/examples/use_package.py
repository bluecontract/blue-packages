#!/usr/bin/env python3
"""Read the built package, mount selected names, and create a local typed document."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from package_core import read_package,mount
from blue_language import Language

package=read_package(ROOT/'dist/package.bluepkg')
blue=Language(core_contracts=False)
mount(blue,package,'@blue/language',['Package','Protocol Specification'])

definition=blue.admit_definition(json.dumps({
    'name':'Delivery Note',
    'description':'A local definition; no generated application class is required.',
    'reference':{'type':'Text'},
    'quantity':{'type':'Integer','schema':{'minimum':1}},
}))
blue.publish_document(definition)
document=blue.create(json.dumps({
    'type':{'blueId':definition.blue_id},
    'reference':'ORDER-1042',
    'quantity':5,
}))
blue.publish_document(document)
print(json.dumps({
    'packageBlueId':package.manifest['packageBlueId'],
    'mountedNames':sorted(k for k in blue.aliases if k.startswith('@blue/language/')),
    'definitionBlueId':definition.blue_id,
    'documentBlueId':document.blue_id,
    'exact':json.loads(document.exact_text),
    'quantity':blue.query(document.exact_text,'/quantity',mode='exact'),
},indent=2,ensure_ascii=False))
