"""Deterministic, fully specified inputs, unrelated to any private workload."""
from itertools import product

def cascade(depth, retained):
    if not 1<=depth<=11: raise ValueError('depth')
    retained=set(retained)
    if not retained<=set(range(1,depth+1)): raise ValueError('key levels')
    rr={}
    for i in range(depth+1):
        keys=[[0]] if i==0 else ([[0]] if i in retained else [])+[[1,2,3]]
        d={'arity':3 if i==0 else 4,'keys':keys,'fks':[]}
        if i<depth:
            src=[0,1,2] if i==0 else [0,2,3]
            for columns in (src,[src[0],src[2],src[1]]):
                d['fks'].append({'source':columns,'target':f'R{i+1}','columns':[1,2,3]})
        rr[f'R{i}']=d
    queries=[]
    for a,b in ((0,1),(1,0)):
        base=['v:k',f'c:{a}',f'c:{b}']
        queries.append({'atoms':[['R0',base]],'head':['v:k'],'equalities':[]})
        queries.append({'atoms':[['R0',base],['R1',['v:child','v:k',f'c:{a}',f'c:{b}']]],'head':['v:k'],'equalities':[]})
    # Four phases (++--), each with two syntactic representatives.
    states=[]
    for phase in range(4):
        for parity in range(2):
            states.append({'query':(0 if phase<2 else 2)+parity,
                           'next':{'next':2*((phase+1)%4)+parity,'clone':2*phase+1-parity}})
    return {'schema':{'relations':rr},'queries':queries,'alphabet':['next','clone'],
            'states':states,'initial':0,'parameters':{'depth':depth,'retained_identifier_keys':sorted(retained)}}

def minimum_counts(depth, retained):
    # Formula proved independently in proofs/key_sensitive_bound.md.
    counts=[1]
    retained=set(retained)
    for i in range(1,depth+1):
        counts.append(2*counts[-1] if i==1 or i-1 in retained else 2)
    return counts

def minimum_witness(depth,retained,limit=128):
    counts=minimum_counts(depth,retained)
    if sum(counts)>limit: return {'status':'BOUND_REJECTED_NOT_MATERIALIZED','minimum':sum(counts),'level_counts':counts}
    retained=set(retained); db={'R0':[[2,0,1]]}; nxt=10
    for i in range(1,depth+1):
        parents=db[f'R{i-1}']; keys=set()
        for row in parents:
            k,a,b=(row[0],row[1],row[2]) if i==1 else (row[0],row[2],row[3])
            keys.add((k,a,b));keys.add((k,b,a))
        tuples=[]
        for key in sorted(keys):
            ident=nxt if i in retained else 2
            if i in retained:nxt+=1
            tuples.append([ident,*key])
        db[f'R{i}']=tuples
    assert [len(db[f'R{i}']) for i in range(depth+1)]==counts
    return {'status':'MATERIALIZED','minimum':sum(counts),'level_counts':counts,'database':db}

def plan():
    out=[]
    for d in range(1,7): out.append((d,list(range(1,d+1)),'all-identifier-keys'))
    for d in range(1,7): out.append((d,[],'no-nonroot-identifier-keys'))
    for kept in ([1,3,5],[2,4,6],[1,2,4,5],[1,2,3,4,5]): out.append((6,kept,'mixed-identifier-keys'))
    return out
