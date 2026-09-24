"""Separately implemented certificate verifier; it does not import the producer.

Acceptance is evidence relative to the supplied schema, queries and transition
system. It is not an independent blind review or a machine-checked metatheorem.
"""
from itertools import combinations, product

class InvalidCertificate(ValueError):
    pass

class VerificationLimit(Exception):
    pass

def require(condition,message):
    if not condition: raise InvalidCertificate(message)

def literal(t):
    return isinstance(t,str) and t.startswith('c:')

def trusted_input(m):
    rel=m['schema']['relations']
    require(0<len(rel)<=12,'schema size')
    for r,d in rel.items():
        require(isinstance(r,str) and 1<=d['arity']<=16,'relation')
        require(bool(d['keys']),'missing key')
        for k in d['keys']:
            require(bool(k) and len(set(k))==len(k) and all(type(c) is int and 0<=c<d['arity'] for c in k),'key')
        for f in d.get('fks',[]):
            require(f['target'] in rel,'target')
            require(f['columns'] in rel[f['target']]['keys'],'target is not a declared key')
            require(len(f['source'])==len(f['columns']) and len(set(f['source']))==len(f['source']),'foreign key width')
            require(all(type(c) is int and 0<=c<d['arity'] for c in f['source']),'foreign key source')
    require(0<len(m['queries'])<=64,'query count')
    arities=set()
    for q in m['queries']:
        require(0<len(q['atoms'])<=12,'atom count')
        variables=set()
        for r,row in q['atoms']:
            require(r in rel and len(row)==rel[r]['arity'],'atom shape')
            for t in row:
                require(isinstance(t,str) and (t.startswith('v:') or literal(t)),'term')
                if literal(t): require(str(int(t[2:]))==t[2:],'noncanonical integer')
                else: variables.add(t)
        require(all(isinstance(pair,list) and len(pair)==2 for pair in q.get('equalities',[])),'equality shape')
        for t in q['head']+sum(q.get('equalities',[]),[]):
            require(literal(t) or t in variables,'unsafe output or guard')
            if literal(t):require(str(int(t[2:]))==t[2:],'noncanonical integer')
        arities.add(len(q['head']))
    require(len(arities)==1,'output arity')
    require(0<len(m['states'])<=4096 and 0<len(m['alphabet'])<=16,'machine size')
    require(len(m['alphabet'])==len(set(m['alphabet'])),'alphabet duplicates')
    require(type(m['initial']) is int and 0<=m['initial']<len(m['states']),'initial')
    for s in m['states']:
        require(type(s['query']) is int and 0<=s['query']<len(m['queries']),'output label')
        require(set(s['next'])==set(m['alphabet']),'total transitions')
        require(all(type(t) is int and 0<=t<len(m['states']) for t in s['next'].values()),'target state')

def checked_chase(q,sch,cc):
    rows=cc['rows']; rel=sch['relations']
    require(len(q['atoms'])<=len(rows)<=256,'certificate record cap')
    symbols=set(t for _,ts in q['atoms'] for t in ts)
    symbols.update(q['head']); symbols.update(sum(q.get('equalities',[]),[]))
    used_edges=set()
    for i,entry in enumerate(rows):
        if i<len(q['atoms']):
            r,ts=q['atoms'][i]
            require(entry=={'rel':r,'terms':ts,'origin':['seed',i]},'seed changed')
        else:
            origin=entry['origin']; require(len(origin)==3 and origin[0]=='fk','origin')
            _,parent,edge=origin
            require(type(parent) is int and 0<=parent<i and type(edge) is int,'parent order')
            source=rows[parent]
            fs=rel[source['rel']].get('fks',[])
            require(0<=edge<len(fs) and (parent,edge) not in used_edges,'FK use')
            used_edges.add((parent,edge));f=fs[edge]
            expected=[f'n:{i}:{c}' for c in range(rel[f['target']]['arity'])]
            for s,d in zip(f['source'],f['columns']):expected[d]=source['terms'][s]
            require(entry['rel']==f['target'] and entry['terms']==expected,'FK expansion')
            for c,t in enumerate(expected):
                if c not in f['columns']:require(t not in symbols,'freshness')
            symbols.update(expected)
    require(used_edges=={(i,e) for i,r in enumerate(rows) for e in range(len(rel[r['rel']].get('fks',[])))},'incomplete FK unfolding')
    # Flat class rewriting is deliberately different from the producer's union-find.
    eq={t:t for t in symbols}
    def v(t):
        require(t in eq,'unknown symbol');return eq[t]
    for step,u in enumerate(cc['unions']):
        a,b=u['left'],u['right'];why=u['reason']
        if why[0]=='guard':
            require(len(why)==2 and type(why[1]) is int and 0<=why[1]<len(q.get('equalities',[])),'guard index')
            require([a,b]==q['equalities'][why[1]],'guard changed')
        elif why[0]=='key':
            require(len(why)==5,'key reason')
            _,i,j,k,c=why
            require(all(type(z) is int for z in (i,j,k,c)) and 0<=i<len(rows) and 0<=j<len(rows),'key record')
            x,y=rows[i],rows[j]
            require(x['rel']==y['rel'],'key relation')
            ks=rel[x['rel']]['keys'];require(0<=k<len(ks),'key number')
            require(all(v(x['terms'][z])==v(y['terms'][z]) for z in ks[k]),'key premise')
            require(0<=c<len(x['terms']) and [a,b]==[x['terms'][c],y['terms'][c]],'key consequence')
        else:raise InvalidCertificate('unknown equality reason')
        aa,bb=v(a),v(b)
        if aa==bb:continue
        if literal(aa) and literal(bb):
            require(cc['unsat'] is True and step==len(cc['unions'])-1,'invalid clash status')
            return {'unsat':True,'facts':{},'head':None}
        canonical=min((aa,bb),key=lambda t:(not literal(t),t))
        eq={t:(canonical if z in (aa,bb) else z) for t,z in eq.items()}
    require(cc['unsat'] is False,'unjustified unsatisfiability')
    require(all(v(a)==v(b) for a,b in q.get('equalities',[])),'unguarded equality')
    facts={r:set() for r in rel}
    for row in rows:facts[row['rel']].add(tuple(v(t) for t in row['terms']))
    require(sum(map(len,facts.values()))<=128,'normalized instance cap')
    for r,tuples in facts.items():
        for key in rel[r]['keys']:
            groups={}
            for row in tuples:
                pk=tuple(row[c] for c in key)
                require(pk not in groups or groups[pk]==row,'not key-saturated')
                groups[pk]=row
        for f in rel[r].get('fks',[]):
            targets={tuple(row[c] for c in f['columns']) for row in facts[f['target']]}
            require(all(tuple(row[c] for c in f['source']) in targets for row in tuples),'not FK-saturated')
    return {'unsat':False,'facts':facts,'head':tuple(v(t) for t in q['head'])}

def checked_map(p,q,cp,proof):
    require(proof is not None,'missing positive containment proof')
    if proof.get('kind')=='vacuous':
        require(cp['unsat'],'spurious vacuity');return
    require(proof.get('kind')=='map' and not cp['unsat'],'containment kind')
    env=proof['mapping']
    vv={t for _,row in q['atoms'] for t in row if not literal(t)}
    require(set(env)==vv,'mapping domain')
    domain={t for rows in cp['facts'].values() for row in rows for t in row}
    require(all(t in domain for t in env.values()),'mapping range')
    term=lambda t:t if literal(t) else env[t]
    for r,row in q['atoms']:require(tuple(term(t) for t in row) in cp['facts'].get(r,set()),'mapping atom')
    require(all(term(a)==term(b) for a,b in q.get('equalities',[])),'mapping guard')
    require(tuple(term(t) for t in q['head'])==cp['head'],'mapping output')

def legal_database(sch,db,cap=128):
    rel=sch['relations']
    require(set(db)<=set(rel),'unexpected relation')
    require(sum(len(ts) for ts in db.values())<=cap,'witness cap')
    for r,d in rel.items():
        rows=db.get(r,[])
        require(all(len(t)==d['arity'] and all(type(v) is int for v in t) for t in rows),'ground tuple')
        require(len({tuple(t) for t in rows})==len(rows),'duplicate set tuple')
        for key in d['keys']:
            seen=set()
            for t in rows:
                k=tuple(t[c] for c in key);require(k not in seen,'ground key violation');seen.add(k)
        for f in d.get('fks',[]):
            targets={tuple(t[c] for c in f['columns']) for t in db.get(f['target'],[])}
            require(all(tuple(t[c] for c in f['source']) in targets for t in rows),'ground FK violation')
    return True

def evaluate(q,db):
    """Independent set evaluator: original atom order and eager partial guards."""
    partial=[{}]
    for r,terms in q['atoms']:
        nxt=[]
        for env in partial:
            for values in db.get(r,[]):
                e=dict(env);good=True
                for t,a in zip(terms,values):
                    if literal(t):
                        if int(t[2:])!=a:good=False;break
                    elif t in e:
                        if e[t]!=a:good=False;break
                    else:e[t]=a
                if good:
                    for a,b in q.get('equalities',[]):
                        if (literal(a) or a in e) and (literal(b) or b in e):
                            x=int(a[2:]) if literal(a) else e[a]
                            y=int(b[2:]) if literal(b) else e[b]
                            if x!=y:good=False;break
                if good:nxt.append(e)
        partial=nxt
    result=set()
    for env in partial:
        term=lambda t:int(t[2:]) if literal(t) else env[t]
        if all(term(a)==term(b) for a,b in q.get('equalities',[])):
            result.add(tuple(term(t) for t in q['head']))
    return result

def verify(m,c):
    trusted_input(m)
    require(len(c['chases'])==len(m['queries']),'chase count')
    cp=[checked_chase(q,m['schema'],z) for q,z in zip(m['queries'],c['chases'])]
    required_entries={f'{i},{j}' for i in range(len(cp)) for j in range(len(cp))}
    require(set(c['containment'])==required_entries,'containment matrix coverage')
    # Every missing homomorphism is checked as a concrete non-containment witness.
    # This is independent relational evaluation, not trust in a failed producer search.
    numeric=[]
    for image in cp:
        if image['unsat']:
            numeric.append(None);continue
        symbols={t for tuples in image['facts'].values() for row in tuples for t in row}
        symbols.update(image['head'])
        constants={int(t[2:]) for q in m['queries'] for _,row in q['atoms'] for t in row if literal(t)}
        constants.update(int(t[2:]) for q in m['queries'] for t in q['head']+sum(q.get('equalities',[]),[]) if literal(t))
        first=max(constants|{1})+1
        names={t:first+k for k,t in enumerate(sorted(t for t in symbols if not literal(t)))}
        value=lambda t:int(t[2:]) if literal(t) else names[t]
        db={r:[[value(t) for t in row] for row in sorted(tuples)] for r,tuples in image['facts'].items()}
        legal_database(m['schema'],db)
        numeric.append((db,tuple(value(t) for t in image['head'])))
    for key,proof in c['containment'].items():
        i,j=map(int,key.split(','))
        if proof is not None:
            checked_map(m['queries'][i],m['queries'][j],cp[i],proof)
        else:
            require(numeric[i] is not None,'empty source cannot witness non-containment')
            db,head=numeric[i]
            require(head in evaluate(m['queries'][i],db),'source witness missing')
            require(head not in evaluate(m['queries'][j],db),'false non-containment')
    reached={m['initial']};front=[m['initial']]
    for s in front:
        for a in m['alphabet']:
            t=m['states'][s]['next'][a]
            if t not in reached:reached.add(t);front.append(t)
    blocks=c['blocks'];flat=[s for b in blocks for s in b]
    require(all(blocks) and len(flat)==len(set(flat)) and set(flat)==reached,'partition coverage')
    cl={s:i for i,b in enumerate(blocks) for s in b}
    for b in blocks:
        for s in b:
            i=m['states'][b[0]]['query'];j=m['states'][s]['query']
            for x,y in ((i,j),(j,i)):
                checked_map(m['queries'][x],m['queries'][y],cp[x],c['containment'].get(f'{x},{y}'))
            for a in m['alphabet']:
                require(cl[m['states'][s]['next'][a]]==cl[m['states'][b[0]]['next'][a]],'not a congruence')
    if len(blocks)*(len(blocks)-1)//2 > 500000:
        raise VerificationLimit('separator-pair admission limit')
    need=set(combinations(range(len(blocks)),2));seen=set()
    for sep in c['separators']:
        pair=tuple(sep['blocks']);require(pair in need and pair not in seen,'separator pair')
        seen.add(pair);s,t=(blocks[i][0] for i in pair)
        require(len(sep['word'])<=max(0,len(reached)*(len(reached)-1)//2-1),'trace cap')
        for a in sep['word']:
            require(a in m['alphabet'],'trace action')
            s=m['states'][s]['next'][a];t=m['states'][t]['next'][a]
        db=sep['database'];legal_database(m['schema'],db)
        q=m['queries'][m['states'][s]['query']];p=m['queries'][m['states'][t]['query']]
        require(evaluate(q,db)!=evaluate(p,db),'non-separating database/trace')
    require(seen==need,'missing minimality witnesses')
    return {'reachable_states':len(reached),'quotient_states':len(blocks),
            'separator_pairs':len(seen),'maximum_trace_length':max((len(x['word']) for x in c['separators']),default=0)}
