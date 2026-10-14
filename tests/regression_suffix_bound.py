"""Supplementary finite regressions for Q4's refinement bound."""
from itertools import combinations, product
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from workload_identifiability.core import partition, reachable, suffix


def unary_machine(transitions):
    return {
        "initial": 0, "alphabet": ["step"],
        "states": [{"query": i, "next": {"step": t}}
                   for i, t in enumerate(transitions)],
    }


class SuffixBoundTests(unittest.TestCase):
    def test_all_binary_output_unary_machines_through_four_states(self):
        machines = 0
        for n in range(1, 5):
            for transitions in product(range(n), repeat=n):
                model = unary_machine(transitions)
                states = reachable(model)
                for labels in product(range(2), repeat=n):
                    blocks, _ = partition(model, labels)
                    classes = {s: i for i, block in enumerate(blocks) for s in block}
                    c0 = len({labels[s] for s in states})
                    for s, t in combinations(states, 2):
                        if classes[s] == classes[t]:
                            with self.assertRaisesRegex(ValueError, "no separating"):
                                suffix(model, s, t, labels)
                        else:
                            word, x, y = suffix(model, s, t, labels)
                            self.assertLessEqual(len(word), len(states) - c0)
                            self.assertNotEqual(labels[x], labels[y])
                    machines += 1
        self.assertEqual(machines, 4330)

    def test_chain_attains_n_minus_two(self):
        for n in range(2, 9):
            model = unary_machine(tuple(range(1, n)) + (n - 1,))
            labels = [0] * (n - 1) + [1]
            word, _, _ = suffix(model, 0, 1, labels)
            self.assertEqual(len(word), n - 2)


if __name__ == "__main__":
    unittest.main()
