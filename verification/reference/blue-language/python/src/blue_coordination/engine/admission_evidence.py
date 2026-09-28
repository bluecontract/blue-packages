"""Protected local Language admission evidence, separate from content bytes.

Only a successful host admission issues a row. Rows are published atomically
with their retained content. Public Content imports cannot supply this family.
This is not signature/authority evidence, and never changes Contracts gas.
"""
from collections import OrderedDict
from algorithms import blue as L
from blue_language.prepared import binding
from blue_coordination_spec.model import require
from .store import fingerprint

FORMAT = 'coordination.language-admission/1'


class _AnnotationEvidence:
    """Reuse a closed value under purely descriptive declaration parts.

    Language recipes preserve inherited empty/description-only declarations.
    Those parts add no descendant requirements, but their recipe keys differ
    from the bare subject. Validate the actual merged head and presence before
    reusing the already established descendant obligations. Any type, schema,
    value, field, item or container requirement takes ordinary validation.
    """
    def __init__(self, baseline, evidence, context):
        self.baseline,self.evidence,self.context=baseline,evidence,context

    def __contains__(self, key):
        if key in self.baseline:return True
        (parts,requirements),goal,is_root=key
        if requirements or len(parts)<2 or any('#' in part for part in parts):return False
        if self.evidence.lookup(parts[-1]) is None:return False
        for part in parts[:-1]:
            body=L.open_exact(L.Ref(part),self.context)
            if any(name not in ('name','description') for name,_ in body.fields):return False
        L.open_exact(L.Ref(parts[-1]),self.context)
        recipe=L.Recipe(tuple(L.Ref(part) for part in parts))
        head=L.head(recipe,self.context)
        L.validate_schema(head,True if is_root else L.concrete(head,self.context),goal,is_root,self.context)
        self.baseline.add(key)
        return True

    def add(self, key):self.baseline.add(key)
    def update(self, keys):self.baseline.update(keys)
    def __iter__(self):return iter(self.baseline)
    def __len__(self):return len(self.baseline)


class AdmissionEvidence:
    def __init__(self, language):
        self.language=language
        self.policy=binding()['policy']
        self.rows=OrderedDict()
        self.dirty={}
        self.store=None

    def bind(self, view):
        store=view.store if view is not None else self.store
        if self.store is not None and store is not self.store:
            self.rows.clear();self.dirty.clear()
        self.store=store

    def lookup(self, identity):
        if '#' in identity:return None  # Cyclic owning-set evidence uses the reference.
        row=self.rows.get(identity)
        if row is None and self.language.view is not None:
            row=self.language.view.get('language_admissions',identity)
        if row is not None:
            require(type(row) is dict and set(row)=={'format','subject','policy','goal','digest'},
                'CORRUPT_LANGUAGE_ADMISSION')
            body={k:v for k,v in row.items() if k!='digest'}
            require(row['format']==FORMAT and row['subject']==identity and row['policy']==self.policy and
                row['goal']=='value' and row['digest']==fingerprint(body),'CORRUPT_LANGUAGE_ADMISSION')
            self.rows[identity]=row;self.rows.move_to_end(identity)
            while len(self.rows)>8192:self.rows.popitem(last=False)
        return row

    def issue(self, node):
        identity=L.identity(node)
        if '#' in identity or identity in self.rows:return
        body=dict(format=FORMAT,subject=identity,policy=self.policy,goal='value')
        row={**body,'digest':fingerprint(body)}
        self.rows[identity]=row;self.dirty[identity]=row
        while len(self.rows)>8192:self.rows.popitem(last=False)

    def certify(self, exact, context, goal='value'):
        original=context.validation_cache
        context.validation_cache=_AnnotationEvidence(original,self,context)
        try:return self._certify(exact,context,goal)
        finally:context.validation_cache=original

    def _certify(self, exact, context, goal='value'):
        """Strict admission with exact, context-free subtree evidence reuse.

        Additional container/type requirements retain their distinct Recipe key
        and run the ordinary Language validator. No invalid/incomplete result
        becomes evidence. The reference handles cyclic and pinned-body inputs.
        """
        L.require(goal in ('definition','value'),'InvalidOperation','validation goal')
        pending=[(exact,context.diagnostic_path)];seen=set();types={};key_types={}
        while pending:
            node,path=pending.pop()
            with L.error_scope(context,path,'dependency-verification'):
                identity=L.identity(node);context.step()
                if identity in seen:continue
                seen.add(identity)
                if '#' in identity or isinstance(node,L.Ref) and node.body is not None:
                    L.strict_certify(exact,context,goal)
                    if goal=='value':self.issue(exact)
                    return
                known=self.lookup(identity)
                if known is not None:
                    # Verify this demanded manifest against the captured resolver.
                    # The proof covers its closed descendants, not a new recipe.
                    L.open_exact(node,context)
                    recipe=L.recipe(node)
                    h=L.head(recipe,context)
                    nested=L.concrete(h,context) or not h.constraints.required
                    for admitted_goal in ('definition','value'):
                        context.validation_cache.add((recipe.key(),admitted_goal,True))
                        if nested:context.validation_cache.add((recipe.key(),admitted_goal,False))
                    continue
                body=L.open_exact(node,context)
                children=[]
                for key,value in body.fields:
                    if key in L.TYPES:
                        L.require(isinstance(value,L.Ref),'InvalidNodeShape','type position')
                        at=L.pointer(path,key);types.setdefault(value.id,at);children.append((value,at))
                        if key=='keyType':key_types.setdefault(value.id,at)
                    elif key=='items':
                        children.extend((item,L.pointer(L.pointer(path,key),i)) for i,item in enumerate(value))
                    elif key not in L.LITERALS|{'mergePolicy'}:children.append((value,L.pointer(path,key)))
                pending.extend(reversed(children))
        for identity in sorted(types):
            if identity not in L.CORE_NAME:
                with L.error_scope(context,types[identity],'type-definition'):
                    L.certify(L.Ref(identity),context,'definition')
        for identity in sorted(key_types):
            with L.error_scope(context,key_types[identity],'type-definition'):
                L.require(L.domain_core(identity,context) in ('Text','Integer','Double','Boolean'),
                    'TypeCompatibilityViolation','keyType')
        L.certify(exact,context,goal)
        if goal=='value':self.issue(exact)
