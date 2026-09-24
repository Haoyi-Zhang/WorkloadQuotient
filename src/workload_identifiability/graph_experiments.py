"""Deterministic graph/image controls fixed after the image pilot.

These are generated instances, never substitutes for admitted public SQL.
The chromatic oracle does not import the homomorphic-image enumerator.
"""
from pathlib import Path
from itertools import combinations
import csv, json, resource, time
from .experiments import apply_limits, dump
from .graphs import graph_model, graph_plan, chromatic_oracle, coloring_witness
from .images import minimum_image
from .core import produce, BoundExceeded
from .verify import verify, legal_database, evaluate, InvalidCertificate


def campaign(out: Path):
    if out.exists():
        raise FileExistsError('Choose a new graph output directory.')
    apply_limits(); out.mkdir(parents=True)
    start=time.process_time();wall=time.monotonic()
    rows=[];partitions=0;oracle_assignments=0;all_checks=0

    def one(n,edges,retained,name,category):
        nonlocal partitions,oracle_assignments,all_checks
        m=graph_model(n,edges,retained)
        c=produce(m);v=verify(m,c)
        dump(out/'inputs'/f'{name}.json',m)
        dump(out/'results/certificates'/f'{name}.json',c)
        log=out/'results/partitions'/f'{name}.jsonl';log.parent.mkdir(parents=True,exist_ok=True)
        with log.open('w',encoding='utf-8') as f:
            result=minimum_image(m,0,2,record=lambda x:f.write(json.dumps(x,sort_keys=True)+'\n'))
        active=[e for j,e in enumerate(m['parameters']['edges'])
                if j in m['parameters']['retained_secondary_edge_keys']]
        oracle=chromatic_oracle(n,active)
        db=coloring_witness(m,oracle['coloring']);legal_database(m['schema'],db)
        assert evaluate(m['queries'][0],db)=={()} and evaluate(m['queries'][2],db)==set()
        expected=n-1+2*len(m['parameters']['edges'])+oracle['chromatic_number']
        assert result['complete'] and result['minimum']==expected==sum(map(len,db.values()))
        dump(out/'results/images'/f'{name}.json',result)
        dump(out/'results/coloring-oracle'/f'{name}.json',{'oracle':oracle,'database':db,'expected_minimum':expected})
        partitions+=result['partitions'];oracle_assignments+=oracle['assignments_tested']
        all_checks+=16+len(m['states'])*(len(c['refinement_sizes'])+1)
        if partitions+all_checks>500000:raise BoundExceeded('aggregate graph obligation cap')
        rows.append({'case':name,'category':category,'vertices':n,'edges':len(m['parameters']['edges']),
                     'retained_secondary_keys':len(m['parameters']['retained_secondary_edge_keys']),
                     'relations':len(m['schema']['relations']),
                     'maximum_query_atoms':max(len(q['atoms']) for q in m['queries']),
                     'quotient_states':v['quotient_states'],'chromatic_number':oracle['chromatic_number'],
                     'minimum_tuples':result['minimum'],'canonical_tuples':n-1+2*len(edges)+n,
                     'partitions':result['partitions'],'legal_partitions':result['legal_images'],
                     'minimizing_partitions':result['minimizing_partitions'],
                     'oracle_assignments':oracle['assignments_tested'],
                     'charged_search_obligations':c['charged_search_obligations']})
        return m,result

    for i,(n,edges,name) in enumerate(graph_plan(),1):
        one(n,edges,None,f'graph-{i:02d}','graph-control')
    for n,edges,label in [(3,[(0,1),(0,2),(1,2)],'triangle'),
                           (4,[(0,1),(0,3),(1,2),(2,3)],'cycle')]:
        for mask in range(1<<len(edges)):
            kept=[j for j in range(len(edges)) if (mask>>j)&1]
            one(n,edges,kept,f'key-ablation-{label}-{mask:02d}','key-ablation')

    # Equal-size, nonisomorphic globally minimum databases. T1 is diagonal
    # in one and non-diagonal in the other; every isomorphism preserves this.
    mm=graph_model(4,[(0,1),(2,3)])
    d1=coloring_witness(mm,[0,1,0,1]);d2=coloring_witness(mm,[0,1,1,0])
    for db in (d1,d2):
        legal_database(mm['schema'],db)
        assert evaluate(mm['queries'][0],db)=={()}
    assert sum(map(len,d1.values()))==sum(map(len,d2.values()))==9
    assert d1['T1'][0][0]!=d1['T1'][0][1] and d2['T1'][0][0]==d2['T1'][0][1]
    dump(out/'results/nonunique-optimum.json',{
        'model':mm,'first':d1,'second':d2,'minimum':9,
        'isomorphism_obstruction':'The sole T1 tuple has unequal coordinates in the first database and equal coordinates in the second.'})
    bad=coloring_witness(mm,[0,0,1,1]);reason=None
    try:legal_database(mm['schema'],bad)
    except InvalidCertificate as e:reason=str(e)
    assert reason is not None
    dump(out/'results/adjacent-color-mutation.json',{'model':mm,'database':bad,'rejected':True,'reason':reason})

    with (out/'results/graphs.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    swap=0
    for line in Path('/proc/self/status').read_text().splitlines():
        if line.startswith('VmSwap:'):swap=int(line.split()[1])
    assert swap==0
    report={'graph_families':8,'key_ablation_instances':24,'checked_instances':len(rows),
            'image_partitions':partitions,'coloring_assignments':oracle_assignments,
            'producer_charged_search_obligations':sum(r['charged_search_obligations'] for r in rows),
            'equivalence_and_signature_obligations':all_checks,'directed_containment_checks':16*len(rows),
            'separator_checks':6*len(rows),'all_exact_minima_match_color_oracle':True,
            'adjacent_color_mutations_rejected':1,'nonisomorphic_optima':2,
            'cpu_seconds':time.process_time()-start,'wall_seconds':time.monotonic()-wall,
            'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'process_swap_kib':swap,'workers':1,'randomness':'none',
            'scope':'Generated bounded instances; not a database-engine replay or proof of the general theorems.'}
    dump(out/'results/graph-campaign.json',report)
    return report
