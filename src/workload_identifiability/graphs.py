"""Graph-coloring witnesses with connected acyclic queries and unary FKs."""
from itertools import product
from copy import deepcopy

def graph_model(n,edges,retained=None):
    if not 2<=n<=6:raise ValueError('generated graph vertex bound')
    edges=sorted(set(tuple(sorted(e)) for e in edges))
    if any(len(e)!=2 or e[0]==e[1] or not 0<=e[0]<e[1]<n for e in edges):raise ValueError('simple graph')
    retained=set(range(len(edges))) if retained is None else set(retained)
    if not retained<=set(range(len(edges))):raise ValueError('key subset')
    rr={'C':{'arity':1,'keys':[[0]],'fks':[]}};atoms=[]
    for i in range(n-1):
        r=f'T{i}'
        rr[r]={'arity':2,'keys':[[0,1]],'fks':[
            {'source':[0],'target':'C','columns':[0]},
            {'source':[1],'target':'C','columns':[0]}]}
        atoms.append([r,[f'v:c{i}',f'v:c{i+1}']])
    for j,(a,b) in enumerate(edges):
        r=f'E{j}'
        rr[r]={'arity':3,'keys':[[0,1]]+([[1,2]] if j in retained else []),
               'fks':[{'source':[1],'target':'C','columns':[0]}]}
        atoms.extend([[r,['c:0',f'v:c{a}','c:0']],[r,['c:1',f'v:c{b}','c:0']]])
    q0={'atoms':atoms,'head':[],'equalities':[]}
    q1={'atoms':deepcopy(atoms)+[['C',['v:c0']]],'head':[],'equalities':[]}
    q2={'atoms':[['C',['v:z']]],'head':[],'equalities':[['c:0','c:1']]}
    q3={'atoms':[['C',['v:z']],['C',['v:w']]],'head':[],'equalities':[['c:0','c:1']]}
    states=[{'query':(0 if phase<2 else 2)+parity,
             'next':{'next':2*((phase+1)%4)+parity,'clone':2*phase+1-parity}}
            for phase in range(4) for parity in range(2)]
    return {'schema':{'relations':rr},'queries':[q0,q1,q2,q3],
            'alphabet':['next','clone'],'states':states,'initial':0,
            'parameters':{'vertices':n,'edges':[list(e) for e in edges],
                          'retained_secondary_edge_keys':sorted(retained)}}

def graph_plan():
    return [
        (2,[(0,1)],'edge'),
        (3,[],'edgeless'),
        (3,[(0,1),(1,2)],'path'),
        (3,[(0,1),(0,2),(1,2)],'triangle'),
        (4,[(0,1),(2,3)],'matching'),
        (4,[(0,1),(1,2),(2,3),(0,3)],'four-cycle'),
        (4,[(0,1),(0,2),(1,2),(2,3)],'triangle-with-tail'),
        (5,[(0,1),(1,2),(3,4)],'path-plus-edge')]

def chromatic_oracle(n,edges):
    tested=0
    for k in range(1,n+1):
        for values in product(range(k),repeat=n):
            tested+=1
            if all(values[a]!=values[b] for a,b in edges):
                return {'chromatic_number':k,'coloring':list(values),'assignments_tested':tested}
    raise AssertionError('distinct vertex colors must be valid')

def coloring_witness(model,coloring):
    n=model['parameters']['vertices'];edges=model['parameters']['edges']
    assert len(coloring)==n
    colors=[10+x for x in coloring]
    db={'C':[[x] for x in sorted(set(colors))]}
    for i in range(n-1):db[f'T{i}']=[[colors[i],colors[i+1]]]
    for j,(a,b) in enumerate(edges):db[f'E{j}']=[[0,colors[a],0],[1,colors[b],0]]
    return db
