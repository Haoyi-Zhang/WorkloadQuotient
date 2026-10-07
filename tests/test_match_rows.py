"""Finite join-order checks with an independent literal Cartesian reference.

Portable: imports only this artifact's public modules and standard library.
No prior implementation, private stage path, campaign or engine is required.
"""
import builtins
from copy import deepcopy
from itertools import product
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from workload_identifiability import core
from workload_identifiability.families import cascade
from workload_identifiability.verify import evaluate, verify, InvalidCertificate


def literal_cartesian_matches(query, facts, wanted_head=None, first=False):
    """Enumerate complete row products, not producer backtracking or its cache."""
    atoms = sorted(query["atoms"], key=lambda atom: len(facts.get(atom[0], ())))
    accepted = []
    for rows in product(*(sorted(facts.get(relation, ())) for relation, _ in atoms)):
        assignments = [
            (term, value)
            for (_, terms), row in zip(atoms, rows)
            for term, value in zip(terms, row)
        ]
        variables = list(dict.fromkeys(term for term, _ in assignments
                                       if not term.startswith("c:")))
        env = {term: next(value for name, value in assignments if name == term)
               for term in variables}
        value_of = lambda term: term if term.startswith("c:") else env[term]
        if any(value_of(term) != value for term, value in assignments):
            continue
        if any(value_of(a) != value_of(b) for a, b in query.get("equalities", [])):
            continue
        head = tuple(value_of(term) for term in query["head"])
        if wanted_head is not None and head != tuple(wanted_head):
            continue
        accepted.append(env)
    return accepted[:1] if first else accepted


def query_fixtures():
    return [
        ("projection", {"atoms": [["R", ["v:x", "v:y"]]], "head": ["v:y"]}),
        ("repeated", {"atoms": [["R", ["v:x", "v:x"]]], "head": ["v:x"]}),
        ("constant", {"atoms": [["R", ["c:0", "v:y"]]], "head": ["c:-1", "v:y"]}),
        ("self_join", {"atoms": [["R", ["v:z", "v:x"]], ["R", ["v:x", "v:y"]]],
                       "head": ["v:y", "v:z"]}),
        ("two_relations", {"atoms": [["S", ["v:z", "v:x"]], ["R", ["v:x", "v:y"]]],
                           "head": ["v:z"]}),
        ("guard", {"atoms": [["R", ["v:x", "v:y"]]], "head": ["v:x"],
                   "equalities": [["v:x", "v:y"]]}),
        ("false_boolean", {"atoms": [["R", ["v:x", "v:y"]]], "head": [],
                           "equalities": [["c:0", "c:1"]]}),
        ("true_boolean", {"atoms": [["R", ["v:x", "v:y"]]], "head": []}),
    ]


def finite_corpus():
    rows = list(product(("c:0", "c:1"), repeat=2))
    subsets = [set(row for bit, row in enumerate(rows) if mask & (1 << bit))
               for mask in range(16)]
    for r, s in product(subsets, repeat=2):
        yield {"R": r, "S": s}


class MatchRowsRegression(unittest.TestCase):
    def test_complete_order_and_first_against_literal_products(self):
        calls = 0
        for facts in finite_corpus():
            for name, query in query_fixtures():
                for wanted, first in product((None, ("c:0",), ("c:9",)), (False, True)):
                    with self.subTest(name=name, facts=facts, wanted=wanted, first=first):
                        actual = core.matches(query, facts, wanted, first)
                        expected = literal_cartesian_matches(query, facts, wanted, first)
                        # JSON without sort_keys also checks variable insertion order.
                        self.assertEqual(json.dumps(actual), json.dumps(expected))
                        calls += 1
        self.assertEqual(calls, 12288)

    def test_answers_agree_with_independent_numeric_evaluator(self):
        cases = 0
        for facts in finite_corpus():
            numeric = {r: [[int(t[2:]) for t in row] for row in sorted(rows)]
                       for r, rows in facts.items()}
            for _, query in query_fixtures():
                symbolic = core.answer(query, facts)
                expected = {tuple(f"c:{v}" for v in row) for row in evaluate(query, numeric)}
                self.assertEqual(symbolic, expected)
                cases += 1
        self.assertEqual(cases, 2048)

    def test_stable_ties_duplicates_and_input_immutability(self):
        query = query_fixtures()[4][1]
        facts = {"R": [("c:1", "c:2"), ("c:0", "c:0")],
                 "S": [("c:9", "c:1"), ("c:8", "c:0")]}
        old_query, old_facts = deepcopy(query), deepcopy(facts)
        self.assertEqual(core.matches(query, facts),
                         [{"v:z": "c:8", "v:x": "c:0", "v:y": "c:0"},
                          {"v:z": "c:9", "v:x": "c:1", "v:y": "c:2"}])
        self.assertEqual((query, facts), (old_query, old_facts))
        projection = query_fixtures()[0][1]
        duplicates = {"R": [("c:0", "c:1"), ("c:0", "c:1")]}
        self.assertEqual(len(core.matches(projection, duplicates)), 2)
        self.assertEqual(core.matches(projection, duplicates, first=True),
                         [{"v:x": "c:0", "v:y": "c:1"}])

    def test_relation_sort_reuse_is_call_local_and_lazy(self):
        rows = [("c:1", "c:1"), ("c:0", "c:0")]
        query = {"atoms": [["R", ["v:x", "v:y"]], ["R", ["v:z", "v:w"]]], "head": []}
        calls = []
        def tracked(values, *args, **kwargs):
            if values is rows:
                calls.append("R")
            return builtins.sorted(values, *args, **kwargs)
        with patch.object(core, "sorted", tracked, create=True):
            self.assertEqual(len(core.matches(query, {"R": rows})), 4)
            self.assertEqual(calls, ["R"])
            rows.append(("c:2", "c:2"))
            self.assertEqual(len(core.matches(query, {"R": rows})), 9)
            self.assertEqual(calls, ["R", "R"])
            self.assertEqual(len(core.matches(query, {"R": rows}, first=True)), 1)
            self.assertEqual(calls, ["R", "R", "R"])
        # An empty first relation prevents sorting a later non-comparable input.
        later = {"atoms": [["R", ["v:x", "v:y"]], ["S", ["v:z"]]], "head": []}
        self.assertEqual(core.matches(later, {"R": [], "S": [(0,), ("x",)]}), [])

    def test_certificate_checker_does_not_call_producer(self):
        model = cascade(2, [1, 2])
        cert = core.produce(model)
        expected = {"reachable_states": 8, "quotient_states": 4,
                    "separator_pairs": 6, "maximum_trace_length": 1}
        with patch.object(core, "matches", side_effect=AssertionError("producer used")), \
             patch.object(core, "chase", side_effect=AssertionError("producer used")):
            self.assertEqual(verify(model, cert), expected)
            for field, value in (("separators", []), ("blocks", [[i] for i in range(8)])):
                bad = deepcopy(cert)
                bad[field] = value
                with self.assertRaises(InvalidCertificate):
                    verify(model, bad)
            bad = deepcopy(cert)
            bad["containment"]["0,0"] = None
            with self.assertRaisesRegex(InvalidCertificate, "false non-containment"):
                verify(model, bad)

    def test_admission_caps_and_work_counters_remain_explicit(self):
        model = cascade(2, [1, 2])
        cert = core.produce(model)
        self.assertEqual(cert["charged_search_obligations"], 78)
        self.assertEqual(cert["refinement_sizes"], [2, 4])
        self.assertEqual(cert["syntactic_quotient_size"], 8)
        query = model["queries"][0]
        for limit, message in ((2, "symbolic"),):
            with self.assertRaisesRegex(core.BoundExceeded, message):
                core.chase(query, model["schema"], record_limit=limit)
        with self.assertRaisesRegex(core.BoundExceeded, "normalized"):
            core.chase(query, model["schema"], witness_limit=6)
        self.assertEqual(sum(len(rows) for rows in core.chase(
            query, model["schema"], record_limit=7, witness_limit=7)[1].values()), 7)
        budget = core.WorkBudget(0)
        with self.assertRaises(core.BoundExceeded):
            core.partition(model, [0, 0, 2, 2], budget)
        self.assertEqual(budget.used, 0)
        with self.assertRaisesRegex(core.BoundExceeded, "normalized"):
            core.produce(cascade(7, range(1, 8)))
        with self.assertRaisesRegex(core.BoundExceeded, "symbolic"):
            core.produce(cascade(8, range(1, 9)))


if __name__ == "__main__":
    unittest.main()

