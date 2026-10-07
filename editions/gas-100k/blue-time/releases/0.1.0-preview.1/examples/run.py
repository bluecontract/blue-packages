#!/usr/bin/env python3
"""Run actual Contracts/BEX with explicit, in-memory Time fixture bindings."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from support import Host,REMINDER,ACTIVATION

def main():
    host=Host()
    try:
        init=host.initialize()
        if not init.commits:raise RuntimeError(init.diagnostic)
        rows=[{'stage':'initialized_without_timeline_entry','state':host.business(),
               'requests':host.p.emitted(init),'gas':init.gas}]
        operation=host.invoke()
        if not operation.commits:raise RuntimeError(operation.diagnostic)
        rows.append({'stage':'custom_step_after_operation','state':host.business(),
                     'requests':host.p.emitted(operation),'gas':operation.gas})
        for timestamp in (REMINDER,ACTIVATION):
            host.progress(timestamp,closed_through=timestamp);host.drain()
            rows.append({'stage':'timer_fired','state':host.business(),**host.firings[-1]})
        print(json.dumps({'mode':'conformance_fixture_not_native_scheduler','stages':rows},indent=2))
    finally:host.close()
if __name__=='__main__':main()
