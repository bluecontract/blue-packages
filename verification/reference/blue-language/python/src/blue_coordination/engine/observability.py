"""Physical observations. No counter or host identifier enters semantic input."""
from collections import defaultdict
from contextlib import contextmanager
from contextvars import ContextVar
from threading import RLock

_role=ContextVar('blue_coordination_activity',default='client')

class Metrics(dict):
    def __init__(self,**values):
        super().__init__(values);self.by_role=defaultdict(lambda:defaultdict(float));self.lock=RLock()
    def add(self,key,value=1):
        with self.lock:
            self[key]=self.get(key,0)+value
            self.by_role[_role.get()][key]+=value
    @contextmanager
    def scope(self,role):
        token=_role.set(role)
        try:yield
        finally:_role.reset(token)
    def roles(self):
        with self.lock:return {role:dict(values) for role,values in self.by_role.items()}
