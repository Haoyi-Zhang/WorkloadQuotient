"""Finite regression checks; not a mechanized proof of the general theorems."""
import unittest
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from copy import deepcopy
from itertools import product
from workload_identifiability.core import (validate_model, chase, containment, produce,
    ground, partition, WorkBudget, BoundExceeded)
from workload_identifiability.verify import (verify, checked_chase, legal_database,
    evaluate, InvalidCertificate)
from workload_identifiability.images import minimum_image, partition_count, assignments
from workload_identifiability.families import cascade, minimum_witness, minimum_counts
from workload_identifiability.graphs import graph_model, coloring_witness, chromatic_oracle
from workload_identifiability.experiments import tiny_model, mutation_cases


def single(queries, relations=None):
    if relations is None:
        relations={'R': {'arity': 2, 'keys': [[0]], 'fks': []}}
    return {'schema': {'relations': relations}, 'queries': queries,
            'states': [{'query': i, 'next': {'step': (i+1)%len(queries)}}
                       for i in range(len(queries))],
            'alphabet':['step'], 'initial':0}


def rq(row=('v:x','v:y'),head=('v:x',),equalities=()):
    return {'atoms':[['R',list(row)]], 'head':list(head),
            'equalities':[list(e) for e in equalities]}


class ChaseTests(unittest.TestCase):
    def test_reflexive_containment(self):
        m=single([rq()]); p=m['queries'][0]
        self.assertIsNotNone(containment(p,p,chase(p,m['schema'])))
        self.assertEqual(verify(m,produce(m))['quotient_states'],1)

    def test_fk_join_equivalence(self):
        m=tiny_model(); c=produce(m); verify(m,c)
        self.assertIsNotNone(c['containment']['0,1'])
        self.assertIsNotNone(c['containment']['1,0'])

    def test_child_filter_not_eliminable(self):
        m=tiny_model(); c=produce(m); verify(m,c)
        self.assertIsNone(c['containment']['0,2'])
        self.assertIsNotNone(c['containment']['2,0'])

    def test_key_constant_clash(self):
        p=rq(); p['atoms']=[['R',['c:0','c:0']],['R',['c:0','c:1']]]
        p['head']=[];m=single([p]);c=produce(m)
        self.assertTrue(c['chases'][0]['unsat']);verify(m,c)

    def test_guard_clash(self):
        m=single([rq(head=(),equalities=(('c:0','c:1'),))])
        c=produce(m);self.assertTrue(c['chases'][0]['unsat']);verify(m,c)

    def test_equalities_propagate_through_key(self):
        p=rq();p['atoms'].append(['R',['v:z','c:7']]);p['equalities']=[['v:x','v:z']]
        m=single([p]); c,_,_=chase(p,m['schema']); v=checked_chase(p,m['schema'],c)
        self.assertEqual(len(v['facts']['R']),1)
        self.assertEqual(next(iter(v['facts']['R']))[1],'c:7')

    def test_guard_only_and_head_only_constants_ground_safely(self):
        p=rq(head=('c:9',),equalities=(('c:10','c:10'),))
        q=rq(row=('c:2','v:y'),head=('c:9',))
        m=single([p,q]);c=produce(m);verify(m,c)
        for sep in c['separators']:
            for row in sep['database'].get('R',[]):
                self.assertNotIn(row[0],(2,9,10))

    def test_boolean_true_and_false(self):
        m=single([rq(head=()),rq(head=(),equalities=(('c:0','c:1'),))])
        c=produce(m);self.assertEqual(verify(m,c)['quotient_states'],2)
        self.assertEqual(evaluate(m['queries'][0],{'R':[[5,6]]}),{()})
        self.assertEqual(evaluate(m['queries'][1],{'R':[[5,6]]}),set())

    def test_head_order_is_observable(self):
        m=single([rq(head=('v:x','v:y')),rq(head=('v:y','v:x'))])
        self.assertEqual(verify(m,produce(m))['quotient_states'],2)

    def test_projection_is_set_valued(self):
        q=rq(head=('v:y',)); self.assertEqual(evaluate(q,{'R':[[1,7],[2,7]]}),{(7,)})

    def test_repeated_variable(self):
        q=rq(row=('v:x','v:x'))
        self.assertEqual(evaluate(q,{'R':[[1,1],[2,3]]}),{(1,)})

    def test_negative_constants(self):
        m=single([rq(row=('v:x','c:-3'))]);verify(m,produce(m))

    def test_noncanonical_constants_rejected(self):
        for value in ('c:00','c:-0','c:+1','c: 1','c:1.0'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):validate_model(single([rq(row=(value,'v:y'))]))

    def test_unsafe_head_rejected(self):
        with self.assertRaises(ValueError):validate_model(single([rq(head=('v:absent',))]))

    def test_bad_fk_target_rejected(self):
        m=tiny_model();m['schema']['relations']['R']['fks'][0]['columns']=[1]
        with self.assertRaises(ValueError):validate_model(m)

    def test_query_acyclicity_not_schema_acyclicity(self):
        m=single([rq()]);m['schema']['relations']['R']['fks']=[{'source':[1],'target':'R','columns':[0]}]
        with self.assertRaisesRegex(ValueError,'cyclic dependency'):validate_model(m)

    def test_cyclic_query_rejected(self):
        p=rq();p['atoms']=[['R',['v:x','v:y']],['R',['v:y','v:z']],['R',['v:z','v:x']]]
        with self.assertRaisesRegex(ValueError,'cyclic query'):validate_model(single([p]))

    def test_explicit_equalities_checked_before_acyclicity(self):
        p=rq();p['atoms']=[['R',['v:x','v:y']],['R',['v:y','v:z']],['R',['v:z','v:x']]]
        p['equalities']=[['v:x','v:z']];m=single([p]);validate_model(m);verify(m,produce(m))

    def test_normalized_tuple_cap_unknown(self):
        m=cascade(7,range(1,8))
        with self.assertRaisesRegex(BoundExceeded,'normalized'):produce(m)

    def test_unfolding_cap_unknown(self):
        m=cascade(8,range(1,9))
        with self.assertRaisesRegex(BoundExceeded,'symbolic'):produce(m)


class QuotientTests(unittest.TestCase):
    def test_eight_four_and_two_are_different_objects(self):
        m=cascade(3,[1,2,3]);c=produce(m);v=verify(m,c)
        self.assertEqual((c['syntactic_quotient_size'],c['refinement_sizes'][0],v['quotient_states']),(8,2,4))

    def test_unreachable_states_are_excluded(self):
        m=single([rq()]);m['states'].append({'query':0,'next':{'step':1}})
        v=verify(m,produce(m));self.assertEqual(v['reachable_states'],1)

    def test_all_frozen_mutations_reject(self):
        m=cascade(2,[1,2]);c=produce(m)
        for name,mm,cc in mutation_cases(m,c):
            with self.subTest(name=name):
                with self.assertRaises(InvalidCertificate):verify(mm,cc)

    def test_oversplit_fails_minimality_not_congruence(self):
        m=cascade(2,[1,2]);c=produce(m);c['blocks']=[[i] for i in range(8)];c['separators']=[]
        with self.assertRaisesRegex(InvalidCertificate,'missing minimality'):verify(m,c)

    def test_duplicate_set_tuple_rejected(self):
        with self.assertRaisesRegex(InvalidCertificate,'duplicate set'):
            legal_database(single([rq()])['schema'],{'R':[[1,2],[1,2]]})

    def test_atom_permutation_and_variable_renaming(self):
        m=cascade(2,[1,2]);first=verify(m,produce(m))['quotient_states']
        for q in m['queries']:
            q['atoms'].reverse()
            rename=lambda t:'v:renamed-'+t[2:] if t.startswith('v:') else t
            q['atoms']=[[r,list(map(rename,row))] for r,row in q['atoms']]
            q['head']=list(map(rename,q['head']))
            q['equalities']=[[rename(a),rename(b)] for a,b in q.get('equalities',[])]
        self.assertEqual(verify(m,produce(m))['quotient_states'],first)

    def test_obligation_budget_preflights(self):
        b=WorkBudget(2);b.charge(2)
        with self.assertRaises(BoundExceeded):b.charge(1)
        self.assertEqual(b.used,2)
        with self.assertRaises(BoundExceeded):partition(single([rq()]),[0],WorkBudget(0))


class MinimumTests(unittest.TestCase):
    def test_constant_anchored_fold_is_needed(self):
        p={'atoms':[['R',['v:x','c:0']],['R',['c:0','v:y']]],'head':[]}
        q=rq(head=(),equalities=(('c:0','c:1'),))
        m=single([p,q]);r=minimum_image(m,0,1)
        self.assertEqual(r['minimum'],1);self.assertEqual(r['database']['R'],[[0,0]])

    def test_negative_condition_not_only_legality(self):
        m=single([rq(),rq(row=('v:x','c:0'))])
        log=[];r=minimum_image(m,0,1,record=log.append)
        self.assertTrue(any(x.get('directed_separation') is False for x in log))
        self.assertEqual(r['minimum'],1)

    def test_image_exhaustion_and_equivalence(self):
        m=single([rq(),rq()]);r=minimum_image(m,0,1)
        self.assertEqual(r['status'],'NO_DIRECTED_COUNTEREXAMPLE');self.assertTrue(r['complete'])

    def test_unsatisfiable_source_has_no_image(self):
        m=single([rq(equalities=(('c:0','c:1'),)),rq()]);r=minimum_image(m,0,1)
        self.assertEqual(r['partitions'],0)

    def test_partition_count_matches_enumeration(self):
        for n in range(6):
            for b in range(3):
                self.assertEqual(partition_count(n,b),sum(1 for _ in assignments(n,b)))

    def test_image_cap_never_returns_best_so_far(self):
        m=graph_model(4,[(0,1),(1,2),(2,3),(0,3)])
        with self.assertRaises(BoundExceeded):minimum_image(m,0,2,maximum_partitions=150)

    def test_chromatic_numbers(self):
        for n,edges,k in [(3,[],1),(3,[(0,1),(1,2)],2),(3,[(0,1),(1,2),(0,2)],3)]:
            with self.subTest(edges=edges):self.assertEqual(chromatic_oracle(n,edges)['chromatic_number'],k)

    def test_key_fold_rejected(self):
        m=graph_model(2,[(0,1)]);db=coloring_witness(m,[0,0])
        with self.assertRaisesRegex(InvalidCertificate,'key'):legal_database(m['schema'],db)

    def test_terminal_identifier_key_changes_no_size(self):
        self.assertEqual(minimum_counts(4,[]),minimum_counts(4,[4]))

    def test_cap_checked_before_witness_materialization(self):
        r=minimum_witness(7,range(1,8))
        self.assertEqual(r['minimum'],255);self.assertNotIn('database',r)

    def test_mixed_keys_minimum_is_legal(self):
        m=cascade(6,[1,3,5]);r=minimum_witness(6,[1,3,5])
        self.assertEqual(r['minimum'],19);legal_database(m['schema'],r['database'])

    def test_two_nonisomorphic_optima(self):
        m=graph_model(4,[(0,1),(2,3)])
        a=coloring_witness(m,[0,1,0,1]);b=coloring_witness(m,[0,1,1,0])
        self.assertEqual(sum(map(len,a.values())),9);self.assertEqual(sum(map(len,b.values())),9)
        self.assertNotEqual(a['T1'][0][0],a['T1'][0][1]);self.assertEqual(b['T1'][0][0],b['T1'][0][1])


class PublicEvidenceTests(unittest.TestCase):
    def test_all_public_pairs_collapse(self):
        root=Path(__file__).resolve().parents[1]
        for path in sorted((root/'inputs/public/cases').glob('public-*.json')):
            model=json.loads(path.read_text())
            checked=verify(model,produce(model))
            self.assertEqual(checked['quotient_states'],1,path.name)

    def test_public_manifest_has_eight_unchanged_pairs(self):
        import csv
        import re
        root=Path(__file__).resolve().parents[1]
        data=json.loads((root/'inputs/public/manifest.json').read_text())
        self.assertEqual(data['commit'],'dcc2a91d8971a4c4d30b055f99d7d8428a1b754b')
        self.assertEqual(data['source_path'],'sqlsolver_data/calcite/calcite_tests')
        self.assertEqual(len(data['pairs']),8)
        expected_lines=[[46,47],[78,79],[90,91],[118,119],[120,121],[140,141],[208,209],[360,361]]
        self.assertEqual([p['source_lines'] for p in data['pairs']],expected_lines)

        with (root/'inputs/public-screening.csv').open(newline='') as handle:
            screening=list(csv.DictReader(handle))
        self.assertEqual(len(screening),181)
        self.assertEqual([(int(r['line_a']),int(r['line_b'])) for r in screening],
                         [(2*i,2*i+1) for i in range(181)])
        admitted=[r for r in screening if r['decision']=='ADMIT']
        self.assertEqual([r['public_id'] for r in admitted],[f'public-{i:02d}' for i in range(1,9)])
        self.assertEqual([[int(r['line_a']),int(r['line_b'])] for r in admitted],expected_lines)

        selected=(root/'inputs/public/sqlsolver-selected.sql').read_text()
        comments=re.findall(r'^-- (public-\d+) line (\d+)$',selected,re.M)
        statements=[line[:-1] for line in selected.splitlines()
                    if line.startswith('SELECT ') and line.endswith(';')]
        self.assertEqual(len(comments),16)
        self.assertEqual(len(statements),16)
        expected_comments=[]; expected_sql=[]
        for pair in data['pairs']:
            expected_comments.extend((pair['id'],str(line)) for line in pair['source_lines'])
            expected_sql.extend(pair['sql'])
            case=json.loads((root/'inputs/public/cases'/f"{pair['id']}.json").read_text())
            self.assertEqual(case['provenance']['source_lines'],pair['source_lines'])
            self.assertEqual(case['provenance']['source_sql'],pair['sql'])
            self.assertEqual(case['provenance']['admission_reason'],pair['reason'])
        self.assertEqual(comments,expected_comments)
        self.assertEqual(statements,expected_sql)

    def test_sqlite_public_replay(self):
        from tempfile import TemporaryDirectory
        from workload_identifiability.engine_replay import replay
        root=Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as d:
            result=replay(root,Path(d)/'sqlite.json','sqlite')
        self.assertTrue(result['all_set_results_equal'])
        self.assertTrue(result['all_bag_results_equal'])
        self.assertEqual(result['query_executions'],1024)

if __name__=='__main__':unittest.main()
