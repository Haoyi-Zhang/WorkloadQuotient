"""Certificate producer. All inputs are finite, trusted data, never executable code.

Symbols v:* and n:* are logical variables, c:<integer> are rigid constants.
The executable is deliberately bounded; UNKNOWN is not equivalence.
"""
from __future__ import annotations
from collections import defaultdict, deque
from itertools import combinations
import json

class BoundExceeded(Exception):
    pass

class WorkBudget:
    """Per-production semantic/search obligation ceiling, charged before work."""
    def __init__(self, limit=500000):
        self.limit, self.used = limit, 0
    def charge(self, count):
        if count < 0 or self.used + count > self.limit:
            raise BoundExceeded('semantic/search obligation preflight')
        self.used += count

class Inconsistent(Exception):
    pass

def is_const(t):
    return isinstance(t, str) and t.startswith('c:')

class UF:
    def __init__(self, terms):
        self.p = {t:t for t in terms}
    def find(self, x):
        if x not in self.p:
            self.p[x] = x
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x
    def union(self, a, b):
        a,b = self.find(a), self.find(b)
        if a == b: return False
        if is_const(a) and is_const(b): raise Inconsistent((a,b))
        if is_const(b) or (not is_const(a) and b < a): a,b = b,a
        self.p[b] = a
        return True

def validate_model(m):
    sch=m['schema']; rel=sch['relations']
    if not 1 <= len(rel) <= 12: raise ValueError('relation count')
    ar={r:rel[r]['arity'] for r in rel}
    for r,d in rel.items():
        if not 1 <= d['arity'] <= 16: raise ValueError('arity')
        if not d['keys']: raise ValueError('declared key required')
        for k in d['keys']:
            if not k or len(k)!=len(set(k)) or any(not 0<=j<ar[r] for j in k):
                raise ValueError('key positions')
        for f in d.get('fks',[]):
            t=f['target']; src=f['source']; dst=f['columns']
            if t not in rel or dst not in rel[t]['keys']: raise ValueError('FK target key')
            if len(src)!=len(dst) or len(src)!=len(set(src)) or any(not 0<=j<ar[r] for j in src):
                raise ValueError('FK source positions')
    active=set(); done=set()
    def visit(r):
        if r in active: raise ValueError('cyclic dependency graph is outside the producer fragment')
        if r in done: return
        active.add(r)
        for f in rel[r].get('fks',[]): visit(f['target'])
        active.remove(r); done.add(r)
    for r in rel: visit(r)
    if not 0<len(m['queries'])<=64: raise ValueError('template count')
    def variable(t): return isinstance(t,str) and t.startswith('v:')
    def term(t):
        if variable(t): return True
        if is_const(t):
            try: return str(int(t[2:])) == t[2:]
            except ValueError: pass
        return False
    for q in m['queries']:
        if not 1 <= len(q['atoms']) <= 12: raise ValueError('atom count')
        vs=set()
        for r,row in q['atoms']:
            if r not in rel or len(row)!=ar[r] or not all(map(term,row)): raise ValueError('atom')
            vs.update(t for t in row if variable(t))
        if any(not isinstance(pair,list) or len(pair)!=2 for pair in q.get('equalities',[])): raise ValueError('equality shape')
        for t in q['head']+sum(q.get('equalities',[]),[]):
            if not term(t) or (variable(t) and t not in vs): raise ValueError('unsafe term')
        # GYO alpha-acyclicity after explicit equalities; keys are not used here.
        uf=UF(t for _,row in q['atoms'] for t in row)
        impossible=False
        for a,b in q.get('equalities',[]):
            try: uf.union(a,b)
            except Inconsistent: impossible=True; break
        edges=[set(uf.find(t) for t in row if not is_const(uf.find(t))) for _,row in q['atoms']]
        while edges and not impossible:
            changed=False
            for i,e in enumerate(edges):
                if any(i!=j and e<=f for j,f in enumerate(edges)):
                    edges.pop(i); changed=True; break
            if changed: continue
            counts=defaultdict(int)
            for e in edges:
                for x in e: counts[x]+=1
            reduced=[{x for x in e if counts[x]>1} for e in edges]
            if reduced!=edges: edges=[e for e in reduced if e]; continue
            if any(edges): raise ValueError('cyclic query hypergraph')
            break
    st=m['states']; aa=m['alphabet']
    if len(st)>4096 or not 0<len(aa)<=16 or len(aa)!=len(set(aa)): raise ValueError('state/alphabet bound')
    if not st or not 0<=m['initial']<len(st): raise ValueError('initial state')
    for s in st:
        if not 0<=s['query']<len(m['queries']) or set(s['next'])!=set(aa): raise ValueError('state')
        if any(not 0<=t<len(st) for t in s['next'].values()): raise ValueError('transition')
    if len({len(q['head']) for q in m['queries']})!=1: raise ValueError('common output arity required')

def chase(q, sch, record_limit=256, witness_limit=128):
    """Finite FK-path unfolding, then EGD saturation; certificate, not a canonical core."""
    rel=sch['relations']
    paths={}
    def b(r):
        if r not in paths: paths[r]=1+sum(b(f['target']) for f in rel[r].get('fks',[]))
        return paths[r]
    upper=sum(b(r) for r,_ in q['atoms'])
    if upper>record_limit: raise BoundExceeded('symbolic-record preflight')
    rows=[{'rel':r,'terms':list(ts),'origin':['seed',i]} for i,(r,ts) in enumerate(q['atoms'])]
    i=0
    while i<len(rows):
        row=rows[i]
        for e,f in enumerate(rel[row['rel']].get('fks',[])):
            j=len(rows)
            ts=[f'n:{j}:{c}' for c in range(rel[f['target']]['arity'])]
            for s,d in zip(f['source'],f['columns']): ts[d]=row['terms'][s]
            rows.append({'rel':f['target'],'terms':ts,'origin':['fk',i,e]})
        i+=1
    assert len(rows)==upper
    uf=UF(t for row in rows for t in row['terms'])
    unions=[]
    def merge(a,b,reason):
        if uf.find(a)==uf.find(b): return
        u={'left':a,'right':b,'reason':reason}
        unions.append(u)
        uf.union(a,b)
    try:
        for i,(a,b) in enumerate(q.get('equalities',[])):
            merge(a,b,['guard',i])
        changed=True
        while changed:
            old=len(unions)
            for i,x in enumerate(rows):
                for j in range(i):
                    y=rows[j]
                    if x['rel']!=y['rel']: continue
                    for k,key in enumerate(rel[x['rel']]['keys']):
                        if all(uf.find(x['terms'][c])==uf.find(y['terms'][c]) for c in key):
                            for c,(a,b_) in enumerate(zip(x['terms'],y['terms'])):
                                merge(a,b_,['key',i,j,k,c])
            changed=len(unions)>old
    except Inconsistent:
        return {'rows':rows,'unions':unions,'unsat':True},None,None
    facts=defaultdict(set); size=0
    for r in rows:
        row=tuple(map(uf.find,r['terms']))
        if row not in facts[r['rel']]:
            if size>=witness_limit: raise BoundExceeded('normalized-instance admission')
            facts[r['rel']].add(row);size+=1
    return {'rows':rows,'unions':unions,'unsat':False},dict(facts),tuple(map(uf.find,q['head']))

def matches(q, facts, wanted_head=None, first=False):
    """Indexed relational joins over a finite instance, with rigid constants."""
    atoms=sorted(q['atoms'],key=lambda a:len(facts.get(a[0],())))
    answers=[]
    def rec(i,env):
        if i==len(atoms):
            get=lambda t:t if is_const(t) else env[t]
            if any(get(a)!=get(b) for a,b in q.get('equalities',[])): return False
            if wanted_head is not None and tuple(get(t) for t in q['head'])!=tuple(wanted_head): return False
            answers.append(dict(env)); return first
        r,terms=atoms[i]
        for row in sorted(facts.get(r,())):
            new=dict(env); ok=True
            for t,v in zip(terms,row):
                if is_const(t):
                    if t!=v: ok=False;break
                elif t in new:
                    if new[t]!=v: ok=False;break
                else: new[t]=v
            if ok and rec(i+1,new) and first: return True
        return False
    rec(0,{})
    return answers

def answer(q,facts):
    return {tuple(t if is_const(t) else e[t] for t in q['head']) for e in matches(q,facts)}

def containment(p,q,chased_p):
    cert,db,head=chased_p
    if cert['unsat']: return {'kind':'vacuous'}
    h=matches(q,db,head,True)
    return {'kind':'map','mapping':h[0]} if h else None

def ground(db, model):
    """Injectively interpret every remaining chase name; do not equate SQL NULL with a name."""
    constants={int(t[2:]) for q in model['queries'] for _,row in q['atoms'] for t in row if is_const(t)}
    constants|={int(t[2:]) for q in model['queries'] for t in q['head'] if is_const(t)}
    constants|={int(t[2:]) for q in model['queries'] for pair in q.get('equalities',[]) for t in pair if is_const(t)}
    syms=sorted({t for rs in db.values() for row in rs for t in row if not is_const(t)})
    nxt=max(constants|{1})+1; mp={t:nxt+i for i,t in enumerate(syms)}
    return {r:[[(int(t[2:]) if is_const(t) else mp[t]) for t in row] for row in sorted(rs)] for r,rs in sorted(db.items())}

def reachable(m):
    seen={m['initial']}; todo=[m['initial']]
    for s in todo:
        for a in m['alphabet']:
            t=m['states'][s]['next'][a]
            if t not in seen: seen.add(t);todo.append(t)
    return sorted(seen)

def partition(m,labels,budget=None):
    ss=reachable(m)
    def blocks(sig):
        if budget is not None: budget.charge(len(ss))
        grouped={}
        for s in ss: grouped.setdefault(sig(s),[]).append(s)
        return list(grouped.values())
    pp=blocks(lambda s:labels[m['states'][s]['query']]); history=[len(pp)]
    while True:
        cls={s:i for i,b in enumerate(pp) for s in b}
        nxt=blocks(lambda s:(labels[m['states'][s]['query']],tuple(cls[m['states'][s]['next'][a]] for a in m['alphabet'])))
        if nxt==pp: return pp,history
        pp=nxt;history.append(len(pp))

def suffix(m,s,t,qlabel,budget=None):
    todo=deque([(s,t,[])]); seen={tuple(sorted((s,t)))}
    while todo:
        if budget is not None: budget.charge(1)
        x,y,w=todo.popleft()
        qx=m['states'][x]['query'];qy=m['states'][y]['query']
        if qlabel[qx]!=qlabel[qy]: return w,x,y
        for a in m['alphabet']:
            xx=m['states'][x]['next'][a]; yy=m['states'][y]['next'][a]
            pair=tuple(sorted((xx,yy)))
            if pair not in seen: seen.add(pair);todo.append((xx,yy,w+[a]))
    raise ValueError('no separating suffix')

def produce(m):
    validate_model(m)
    budget=WorkBudget()
    qs=m['queries']; budget.charge(len(qs)**2)
    cp=[chase(q,m['schema']) for q in qs]
    contain={f'{i},{j}':containment(p,q,cp[i]) for i,p in enumerate(qs) for j,q in enumerate(qs)}
    labels=[]
    for i in range(len(qs)):
        equal=[j for j in range(i) if contain[f'{i},{j}'] is not None and contain[f'{j},{i}'] is not None]
        labels.append(labels[equal[0]] if equal else i)
    bb,hist=partition(m,labels,budget)
    budget.charge(len(bb)*(len(bb)-1)//2)
    pairs=[]
    for i,j in combinations(range(len(bb)),2):
        s,t=bb[i][0],bb[j][0]; w,x,y=suffix(m,s,t,labels,budget)
        a,b=m['states'][x]['query'],m['states'][y]['query']
        source=a if contain[f'{a},{b}'] is None else b
        pairs.append({'blocks':[i,j],'word':w,'database':ground(cp[source][1],m)})
    return {'chases':[p[0] for p in cp], 'containment':contain,
            'blocks':bb,'separators':pairs,'refinement_sizes':hist,
            'syntactic_quotient_size':len(partition(m,list(range(len(qs))),budget)[0]),
            'charged_search_obligations':budget.used}
