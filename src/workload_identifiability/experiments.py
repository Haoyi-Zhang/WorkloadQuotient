"""Frozen, deterministic diagnostic campaign. No network, engine or model calls."""
from __future__ import annotations
from copy import deepcopy
from itertools import product, combinations
from pathlib import Path
import csv, json, os, resource, signal, time
from .core import produce, chase, containment, validate_model, BoundExceeded
from .families import cascade, plan, minimum_witness, minimum_counts
from .verify import verify, legal_database, evaluate, InvalidCertificate


def dump(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n',encoding='utf-8')


def tiny_model():
    schema={'relations':{
        'R':{'arity':2,'keys':[[0]],'fks':[{'source':[1],'target':'S','columns':[0]}]},
        'S':{'arity':2,'keys':[[0]],'fks':[]}}}
    qs=[
        {'atoms':[['R',['v:x','v:y']]],'head':['v:x']},
        {'atoms':[['R',['v:x','v:y']],['S',['v:y','v:z']]],'head':['v:x']},
        {'atoms':[['R',['v:x','v:y']],['S',['v:y','c:0']]],'head':['v:x']},
        {'atoms':[['R',['v:x','c:0']]],'head':['v:x']},
        {'atoms':[['R',['v:x','c:1']]],'head':['v:x']},
        {'atoms':[['S',['v:x','v:z']]],'head':['v:x']}]
    states=[{'query':i,'next':{'step':(i+1)%len(qs)}} for i in range(len(qs))]
    return {'schema':schema,'queries':qs,'states':states,'alphabet':['step'],'initial':0}


def tiny_oracle(out):
    m=tiny_model();validate_model(m)
    cp=[chase(q,m['schema']) for q in m['queries']]
    criterion=[[containment(p,q,cp[i]) is not None for q in m['queries']] for i,p in enumerate(m['queries'])]
    dump(out/'inputs/tiny-model.json',m)
    joint=[[True]*len(m['queries']) for _ in m['queries']]
    report=[];total=0
    target=out/'results/tiny-valuations.jsonl';target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('w',encoding='utf-8') as f:
        for n in (2,3):
            domain=range(n)
            functions=[[[k,v] for k,v in enumerate(values) if v!=-1] for values in product(range(-1,n),repeat=n)]
            examined=legal=0;observed=[[True]*len(m['queries']) for _ in m['queries']]
            for r in functions:
                for s in functions:
                    examined+=1;db={'R':r,'S':s}
                    # Independent definition of the only FK, before calling the verifier.
                    if not {row[1] for row in r}<={row[0] for row in s}:continue
                    legal_database(m['schema'],db);legal+=1;total+=1
                    if total>100000:raise BoundExceeded('tiny valuation cap')
                    ans=[evaluate(q,db) for q in m['queries']]
                    for i in range(len(ans)):
                        for j in range(len(ans)):
                            if not ans[i]<=ans[j]:observed[i][j]=False;joint[i][j]=False
                    f.write(json.dumps({'domain_size':n,'database':db,'outputs':[sorted(map(list,a)) for a in ans]},sort_keys=True)+'\n')
            report.append({'domain_size':n,'candidate_databases':examined,'legal_databases':legal,
                           'directed_containment':observed,'matches_complete_criterion':observed==criterion})
    assert joint==criterion
    # Empty-database-only testing incorrectly merges all six queries.
    assert all(evaluate(q,{'R':[],'S':[]})==set() for q in m['queries'])
    result={'domains':report,'legal_databases':total,'query_evaluations':total*len(m['queries']),
            'complete_criterion':criterion,'matches_complete_criterion':joint==criterion,
            'empty_only_false_equivalence_pairs':sum(not (criterion[i][j] and criterion[j][i]) for i,j in combinations(range(6),2)),
            'scope':'Exact only for the recorded finite domains; universal claims use the proof, not this enumeration.'}
    dump(out/'results/tiny-oracle.json',result)
    return result


def mutation_cases(m,c):
    cases=[]
    def add(name,edit):
        mm,cc=deepcopy(m),deepcopy(c);edit(mm,cc);cases.append((name,mm,cc))
    add('delete-required-FK-tuple',lambda m,c:c['separators'][0]['database']['R2'].pop())
    def collide(m,c):
        d=c['separators'][0]['database']['R1'];d[1][0]=d[0][0]
    add('collide-identifier-key',collide)
    add('empty-separating-database',lambda m,c:c['separators'][0].update(database={}))
    add('shorten-distinguishing-word',lambda m,c:c['separators'][0].update(word=[]))
    add('merge-current-equal-future-distinct',lambda m,c:c.update(blocks=[[0,1,2,3],[4,5],[6,7]]))
    add('split-equivalent-states',lambda m,c:c.update(blocks=[[i] for i in range(8)],separators=[]))
    add('remove-positive-containment',lambda m,c:c['containment'].__setitem__('0,1',None))
    add('corrupt-output-map',lambda m,c:c['containment']['0,0']['mapping'].__setitem__('v:k','c:999'))
    add('omit-chase-FK-expansion',lambda m,c:c['chases'][0]['rows'].pop())
    add('forge-unsatisfiable-query',lambda m,c:c['chases'][0].update(unsat=True))
    add('omit-reachable-state',lambda m,c:c['blocks'][0].remove(1))
    add('change-trusted-transition',lambda m,c:m['states'][0]['next'].__setitem__('next',0))
    add('change-trusted-output',lambda m,c:m['queries'][0].update(head=['c:0']))
    add('change-trusted-FK-columns',lambda m,c:m['schema']['relations']['R0']['fks'][0].update(source=[0,2,1]))
    add('false-negative-containment',lambda m,c:c['containment'].__setitem__('0,0',None))
    add('noncanonical-integer',lambda m,c:m['queries'][0]['atoms'][0][1].__setitem__(1,'c:00'))
    return cases


def mutations(out):
    m=cascade(2,[1,2]);c=produce(m);verify(m,c);rows=[]
    for name,mm,cc in mutation_cases(m,c):
        reason=None
        try:verify(mm,cc)
        except InvalidCertificate as e:reason=str(e)
        rows.append({'case':name,'rejected':reason is not None,'reason':reason})
        dump(out/'inputs/mutations'/f'{name}.json',{'model':mm,'certificate':cc})
    if not all(x['rejected'] for x in rows):raise AssertionError([x for x in rows if not x['rejected']])
    dump(out/'results/mutations.json',rows);return rows


def scope_controls(out):
    reports=[]
    for d in range(7,12):
        # This analytic constructor checks the proved count before allocating rows.
        witness=minimum_witness(d,range(1,d+1))
        assert witness['status']=='BOUND_REJECTED_NOT_MATERIALIZED' and 'database' not in witness
        reports.append({'depth':d,**witness,'full_unfolding_records':2**(d+1)-1})
    dump(out/'results/boundary-probes.json',reports)
    return reports


def apply_limits():
    if hasattr(os,'sched_getaffinity'):
        os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS,(int(2.5*1024**3),int(2.5*1024**3)))
    resource.setrlimit(resource.RLIMIT_CPU,(240,240))
    signal.signal(signal.SIGALRM,lambda signum,frame:(_ for _ in ()).throw(TimeoutError('300-second run ceiling')))
    signal.alarm(300)


def campaign(out:Path):
    if out.exists():raise FileExistsError('Choose a new output directory; existing evidence is not overwritten.')
    apply_limits();out.mkdir(parents=True)
    start=time.process_time();wall=time.monotonic();rows=[];obligations=0
    for index,(d,kept,category) in enumerate(plan(),1):
        t=time.process_time();m=cascade(d,kept);c=produce(m);v=verify(m,c)
        w=minimum_witness(d,kept);assert w['status']=='MATERIALIZED'
        legal_database(m['schema'],w['database'])
        assert evaluate(m['queries'][0],w['database'])!=evaluate(m['queries'][2],w['database'])
        key=f'case-{index:02d}'
        dump(out/'inputs/families'/f'{key}.json',m)
        dump(out/'results/certificates'/f'{key}.json',c)
        dump(out/'results/minimum-witnesses'/f'{key}.json',w)
        row={'case':key,'category':category,'depth':d,'retained_identifier_keys':' '.join(map(str,kept)),
             'relations':d+1,'query_templates':len(m['queries']),'reachable_states':v['reachable_states'],
             'syntax_states':c['syntactic_quotient_size'],'current_output_classes':c['refinement_sizes'][0],
             'quotient_states':v['quotient_states'],'separating_pairs':v['separator_pairs'],
             'max_trace_length':v['maximum_trace_length'],
             'max_symbolic_records':max(len(z['rows']) for z in c['chases']),
             'largest_canonical_witness':max(sum(len(rows) for rows in p['database'].values()) for p in c['separators']),
             'minimum_witness':w['minimum'],'charged_search_obligations':c['charged_search_obligations'],'cpu_seconds':time.process_time()-t}
        rows.append(row)
        # Calls to directed containment and state signatures, not all inner tuple comparisons.
        obligations+=len(m['queries'])**2+len(m['states'])*(len(c['refinement_sizes'])+1)
        if obligations>500000:raise BoundExceeded('equivalence/refinement obligation cap')
    (out/'results').mkdir(exist_ok=True)
    with (out/'results/families.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
    tiny=tiny_oracle(out);mut=mutations(out);bound=scope_controls(out)
    swap=0
    if Path('/proc/self/status').exists():
        for line in Path('/proc/self/status').read_text().splitlines():
            if line.startswith('VmSwap:'):swap=int(line.split()[1])
    assert swap==0
    result={'families':len(rows),'directed_family_containment_checks':sum(r['query_templates']**2 for r in rows),
            'family_separator_checks':sum(r['separating_pairs'] for r in rows),
            'equivalence_and_signature_obligations':obligations+36,
            'producer_charged_search_obligations':sum(r['charged_search_obligations'] for r in rows),
            'tiny_legal_valuations':tiny['legal_databases'],'tiny_query_evaluations':tiny['query_evaluations'],
            'mutations_rejected':sum(x['rejected'] for x in mut),'mutations_tested':len(mut),
            'boundary_probes_without_materialization':len(bound),
            'cpu_seconds':time.process_time()-start,'wall_seconds':time.monotonic()-wall,
            'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'process_swap_kib':swap,
            'workers':1,'duckdb_replay':'NOT_RUN_UNAVAILABLE',
            'randomness':'None; all inputs and enumeration order are deterministic.'}
    dump(out/'results/campaign.json',result);signal.alarm(0);return result
