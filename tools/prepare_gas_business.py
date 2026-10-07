#!/usr/bin/env python3
"""Publish business data with the new exact gas-edition dependencies."""
import sys,json
from pathlib import Path
H=Path(__file__).resolve().parents[1];sys.path.insert(0,str(H/'tools'))
from prepare_gas_dependents import *
MAPPING.update(json.loads((H/'editions/gas-10m/mapping.json').read_text()))
foundation={'Language':'blue-language','Contracts':'blue-contracts','Coordination':'blue-coordination'}
with PhysicalCache(65536).scope():
 for name in ['functions/commerce-functions-v1','functions/commerce-functions-v1_1','functions/commerce-functions-v2']:
  prepare(name,name,{'language':'blue-language','contracts':'blue-contracts'})
 for name in ['blue-agreements','clause-mutual-activation','clause-immediate-termination','agreement-reseller','blue-mutual-activation','blue-agreement-examples','blue-mandates','blue-time']:
  cfg=json.loads((H/name/'blue-package.yaml').read_text());deps={}
  known={**foundation,'BEX':'blue-bex','Agreements':'blue-agreements','MutualActivation':'clause-mutual-activation','ImmediateTermination':'clause-immediate-termination'}
  for key in cfg['imports']:deps[key]=next(v for k,v in known.items() if k.lower()==key.lower())
  if name=='blue-mandates':deps['coordination']='editions/gas-10m/blue-coordination'
  prepare(name,name,deps)
(H/'editions/gas-10m/mapping.json').write_bytes(wire(MAPPING))
