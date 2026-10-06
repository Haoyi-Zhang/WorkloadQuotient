"""Finite theorem-boundary checks; no general proof or broad workload claim."""
from itertools import combinations
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from workload_identifiability.core import validate_model
from workload_identifiability.families import cascade, minimum_witness
from workload_identifiability.graphs import graph_model, chromatic_oracle, coloring_witness
from workload_identifiability.images import minimum_image
from workload_identifiability.verify import evaluate, legal_database


class FamilyBoundaries(unittest.TestCase):
    def test_admitted_small_graph_image_minima(self):
        cases = patterns = 0
        for n in range(2, 5):
            possible = list(combinations(range(n), 2))
            for mask in range(1 << len(possible)):
                edges = [edge for bit, edge in enumerate(possible) if mask & (1 << bit)]
                # The positive joined copy has n+2m atoms; retain the existing cap.
                if n + 2*len(edges) > 12:
                    continue
                with self.subTest(n=n, edges=edges):
                    model = graph_model(n, edges)
                    validate_model(model)
                    image = minimum_image(model, 0, 2)
                    oracle = chromatic_oracle(n, edges)
                    expected = n - 1 + 2*len(edges) + oracle["chromatic_number"]
                    self.assertEqual(image["minimum"], expected)
                    self.assertTrue(image["complete"])
                    witness = coloring_witness(model, oracle["coloring"])
                    legal_database(model["schema"], witness)
                    self.assertEqual(evaluate(model["queries"][0], witness), {()})
                    cases += 1
                    patterns += image["partitions"]
        self.assertEqual((cases, patterns), (67, 8923))

    def test_every_small_cascade_key_subset(self):
        cases = 0
        for depth in range(1, 5):
            for mask in range(1 << depth):
                keys = [level for level in range(1, depth+1) if mask & (1 << (level-1))]
                with self.subTest(depth=depth, keys=keys):
                    model = cascade(depth, keys)
                    witness = minimum_witness(depth, keys)
                    legal_database(model["schema"], witness["database"])
                    self.assertEqual(evaluate(model["queries"][0], witness["database"]), {(2,)})
                    self.assertEqual(evaluate(model["queries"][2], witness["database"]), set())
                    # Independently count consecutive keyed-parent suffixes.
                    expected = [1]
                    for level in range(1, depth+1):
                        run = 0
                        for parent in range(level-1, 0, -1):
                            if parent not in keys:
                                break
                            run += 1
                        expected.append(2**(1+run))
                    self.assertEqual(witness["level_counts"], expected)
                    cases += 1
        self.assertEqual(cases, 30)


if __name__ == "__main__":
    unittest.main()
