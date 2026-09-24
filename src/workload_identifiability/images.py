"""Exact bounded homomorphic-image search; no optimum is returned after a cap.

The mathematical completeness argument is in proofs/images_and_hardness.md.
A search is exhaustive over partitions fixing all named constants, not over
subinstances of a particular test database and not over SQL bags.
"""
from functools import lru_cache
from .core import chase,validate_model,BoundExceeded
from .verify import checked_chase,legal_database,evaluate,InvalidCertificate

@lru_cache(None)
def partition_count(remaining,blocks):
    if remaining==0:return 1
    return blocks*partition_count(remaining-1,blocks)+partition_count(remaining-1,blocks+1)

def assignments(n,blocks):
    def rec(prefix,b):
        if len(prefix)==n:
            yield tuple(prefix);return
        for j in range(b):yield from rec(prefix+[j],b)
        yield from rec(prefix+[b],b+1)
    yield from rec([],blocks)

def minimum_image(model,source,target,record=None,maximum_partitions=10000):
    validate_model(model)
    p,q=model['queries'][source],model['queries'][target]
    cc,_,_=chase(p,model['schema'])
    image=checked_chase(p,model['schema'],cc)
    if image['unsat']:
        return {'status':'NO_DIRECTED_COUNTEREXAMPLE','complete':True,'partitions':0}
    constants={t for z in model['queries'] for _,row in z['atoms'] for t in row if t.startswith('c:')}
    constants.update(t for z in model['queries'] for t in z['head']+sum(z.get('equalities',[]),[]) if t.startswith('c:'))
    constants=sorted(constants,key=lambda t:int(t[2:]))
    names=sorted({t for rows in image['facts'].values() for row in rows for t in row if not t.startswith('c:')}|
                 {t for t in image['head'] if not t.startswith('c:')})
    if len(names)>8:raise BoundExceeded('image-search nonconstant-symbol cap; optimality UNKNOWN')
    number=partition_count(len(names),len(constants))
    if number>maximum_partitions:raise BoundExceeded('image-partition preflight; optimality UNKNOWN')
    first=max({int(t[2:]) for t in constants}|{1})+1
    best=None;seen=legal=separating=ties=0
    for blocks in assignments(len(names),len(constants)):
        seen+=1
        mp={t:(int(constants[b][2:]) if b<len(constants) else first+b-len(constants)) for t,b in zip(names,blocks)}
        value=lambda t:int(t[2:]) if t.startswith('c:') else mp[t]
        db={r:sorted(map(list,{tuple(value(t) for t in row) for row in rows})) for r,rows in image['facts'].items()}
        head=tuple(value(t) for t in image['head']);size=sum(map(len,db.values()))
        rejection=None
        try:legal_database(model['schema'],db)
        except InvalidCertificate as e:rejection=str(e)
        info={'partition':list(blocks),'tuples':size,'legal':rejection is None,'rejection':rejection}
        if rejection is None:
            legal+=1
            assert head in evaluate(p,db)
            different=head not in evaluate(q,db)
            info['directed_separation']=different
            if different:
                separating+=1
                if best is None or size<best['minimum']:
                    best={'minimum':size,'database':db,'head':list(head),'partition':list(blocks)};ties=1
                elif size==best['minimum']:ties+=1
        if record is not None:record(info)
    assert seen==number
    result={'status':'EXACT_MINIMUM' if best is not None else 'NO_DIRECTED_COUNTEREXAMPLE',
            'complete':True,'partitions':seen,'legal_images':legal,'separating_images':separating,
            'minimizing_partitions':ties,'source_names':names,'fixed_constants':constants,
            'source_chase':cc,'scope':'Exhaustive legal homomorphic images; theorem supplies global completeness.'}
    if best is not None:result.update(best)
    return result
