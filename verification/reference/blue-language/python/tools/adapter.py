#!/usr/bin/env python3
"""JSONL bridge: receives id/environment/request only, never expected outcomes."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from run import execute
for line in sys.stdin:
    if not line.strip(): continue
    request=json.loads(line)
    if set(request)-{'id','environment','request'}: raise ValueError('invalid request envelope')
    case={**request,'expected':{'outcome':'Established'}}
    print(json.dumps(execute(case),ensure_ascii=False,sort_keys=True),flush=True)
