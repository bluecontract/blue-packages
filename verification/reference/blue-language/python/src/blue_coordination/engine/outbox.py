"""After-commit host delivery. Connectors must deduplicate occurrence identities.

No callback is run by Contracts replay. Acknowledging delivery is a separate,
conditional publication; a crash before acknowledgment can redeliver the same
occurrence, never manufacture a second event identity.
"""
from uuid import uuid4
from .work import publish


class Outbox:
    def __init__(self,store,context='default'):
        self.store,self.context=store,context

    def pending(self,limit=100):
        if type(limit) is not int or not 1<=limit<=1000:raise ValueError('Invalid page size')
        with self.store.read() as view:
            return [dict(identity=key.split('/',1)[1],**row) for key,row in view.scan('outbox',self.context+'/')
                    if not row['acknowledged']][:limit]

    def acknowledge(self,identity,receipt):
        while True:
            with self.store.read() as view:
                key=self.context+'/'+identity;row=view.get('outbox',key)
                if row is None or row['receipt']!=receipt:raise ValueError('Unknown occurrence/receipt pair')
                if row['acknowledged']:return
                packet=view.packet('outbox-ack:'+key,writes={('outbox',key):{**row,'acknowledged':True}})
            if publish(self.store,packet).status=='COMMITTED':return
