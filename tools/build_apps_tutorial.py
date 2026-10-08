#!/usr/bin/env python3
"""Render the current tutorial from its prose and exact public package/example sources."""
import json
from pathlib import Path
from check_clause_tutorial import load
ROOT=Path(__file__).resolve().parents[1]
def code(path):
    return '```yaml\n'+(ROOT/path).read_text().rstrip()+'\n```'
def cell(value):
    return '`'+json.dumps(value,ensure_ascii=False,separators=(',',':')).replace('|','\\|').replace('`','\\`')+'`'
def build():
    intro=(ROOT/'docs/clauses-guide-source.md').read_text()
    families=json.loads((ROOT/'PUBLIC-CLAUSES.json').read_text())['families']
    table='| Family | Public types | Purpose |\n|---|---|---|\n'+'\n'.join('| '+f['name']+' | '+', '.join('`'+t+'`' for t in f['types'])+' | '+f['purpose']+' |' for f in families)
    examples=[]
    for p in sorted((ROOT/'examples/apps').glob('*.blue')):
        text='### '+p.stem+'\n\nSource: [`'+p.name+'`](../examples/apps/'+p.name+').\n\n'+code(p.relative_to(ROOT))
        case=p.with_suffix('.case.yaml')
        if not case.exists():case=p.with_suffix('.native.yaml')
        if case.exists():
            text+='\n\nWalkthrough: [`'+case.name+'`](../examples/apps/'+case.name+'). Targets are relative to the main document; open the named child before invoking its operation.\n\n| Step | Actor | Document | Operation or signal | Input | Expected result |\n|---|---|---|---|---|---|'
            for n,row in enumerate(load(case)['steps'],1):
                expectation='Rejected; no state change' if row.get('status')=='FAILED' else 'Processed'
                if row.get('expect'):expectation+='; '+cell(row['expect'])
                text+='\n| '+str(n)+' | '+str(row.get('source',row.get('channel','—')))+' | '+str(row.get('target','Main'))+' | '+str(row.get('operation','Event'))+' | '+cell(row.get('request',row.get('event',{})))+' | '+expectation+' |'
        else:
            time=p.with_suffix('.time.yaml')
            if time.exists():text+='\n\nSigned-time walkthrough:\n\n'+code(time.relative_to(ROOT))
        examples.append(text)
    text=intro.replace('{{HELLO_SOURCE}}',code('clause-connections/types/hello-clause.blue')).replace('{{PAYMENT_SOURCE}}',code('clause-payment/types/payment-clause.blue')+'\n\nIts complete shared base:\n\n'+code('clause-payment/types/conditional-base.blue')).replace('{{PI_HOST_SOURCE}}',code('payment-instruction/types/host-with-clauses.blue')).replace('{{FAMILY_TABLE}}',table).replace('{{EXAMPLES}}','\n\n'.join(examples))
    (ROOT/'docs/clauses-tutorial.md').write_text(text)
if __name__=='__main__':build()
