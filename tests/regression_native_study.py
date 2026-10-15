"""Native-study component regressions; separate from the frozen Linux census.

Run directly with --work pointing to an existing writable scratch directory.
DuckDB checks are skipped explicitly when its optional package is unavailable.
"""
import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from workload_identifiability import native_study as study
from workload_identifiability.verify import verify

WORK = None
ENGINES = ["sqlite"] + (["duckdb"] if importlib.util.find_spec("duckdb") else [])


class NativeStudyTests(unittest.TestCase):
    def test_retained_results_recompute(self):
        retained = ROOT / "results/native-study"
        summary = json.loads((retained / "summary.json").read_text(encoding="utf-8"))
        records = [json.loads(line) for line in
                   (retained / "trials.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(summary["status"], "NATIVE_STUDY_PASSED")
        self.assertEqual(len(records), 120)
        self.assertEqual(study.summarize(records), summary["rows"])
        keys = {(r["engine"], r["mode"], r["employees"], r["sweeps"], r["repetition"])
                for r in records}
        expected = {(e, m, n, s, r) for e in ("sqlite", "duckdb") for m in study.MODES
                    for n in (128, 1024) for s in (1, 8) for r in range(3)}
        self.assertEqual(keys, expected)
        for record in records:
            stages = ("input_s", "plan_s", "build_load_s", "query_s", "maintenance_s",
                      "validation_s", "checkpoint_close_s", "reopen_validate_s", "unallocated_s")
            self.assertAlmostEqual(sum(record[k] for k in stages), record["total_s"], places=9)
            self.assertGreaterEqual(record["plan_s"], record["produce_s"] + record["verify_s"])
        model = json.loads((retained / "workload.json").read_text(encoding="utf-8"))
        certificate = json.loads((retained / "certificate.json").read_text(encoding="utf-8"))
        self.assertEqual(verify(model, certificate), summary["workload"])

    def test_semantic_quotient_and_same_information_plan(self):
        model, sql, _, _, _ = study.read_inputs(ROOT)
        q = study.plan(model, "quotient_cache")
        o = study.plan(model, "output_cache")
        qo = study.plan(model, "quotient_output_cache")
        self.assertEqual((len(sql), len(model["states"])), (16, 16))
        self.assertEqual((q["routing_states"], q["cache_keys"]), (8, 8))
        self.assertEqual((o["routing_states"], o["cache_keys"]), (16, 4))
        self.assertEqual((qo["routing_states"], qo["cache_keys"]), (8, 4))
        self.assertGreater(q["produce_s"], 0)
        self.assertGreater(o["verify_s"], 0)

    def test_current_outputs_are_not_a_transition_congruence(self):
        model, _, _, _, _ = study.read_inputs(ROOT)
        certificate = study.produce(model)
        self.assertEqual(verify(model, certificate)["quotient_states"], 8)
        c = certificate["containment"]
        # P1 and P3 expose equivalent names now, but their next phases differ.
        self.assertIsNotNone(c["0,4"])
        self.assertIsNotNone(c["4,0"])
        self.assertIsNone(c["2,6"])
        corrupted = deepcopy(certificate)
        corrupted["blocks"] = [[0, 1, 4, 5, 6, 7], [2, 3], [8, 9, 12, 13, 14, 15], [10, 11]]
        with self.assertRaisesRegex(ValueError, "not a congruence"):
            verify(model, corrupted)

    def test_all_methods_and_result_changing_updates(self):
        model, sql, ddl, _, _ = study.read_inputs(ROOT)
        for engine in ENGINES:
            with self.subTest(engine=engine), tempfile.TemporaryDirectory(dir=WORK) as directory:
                db = study.database(32)
                c = study.connect(engine, Path(directory) / "test.db")
                try:
                    study.load(c, ddl, db)
                    previous = None
                    for epoch in range(5):
                        if epoch:
                            study.update(c, db, epoch)
                        answers = study.validate(c, db, model, sql)
                        if previous is not None:
                            self.assertNotEqual(previous, answers)
                        if epoch == 3:
                            self.assertEqual(answers[2], frozenset())
                        for mode, count in zip(study.MODES, (48, 16, 8, 4, 4)):
                            stats = study.requests(c, model, sql, study.plan(model, mode), mode, 3, answers)
                            self.assertEqual(stats["requests"], 48)
                            self.assertEqual(stats["executions"], count)
                        previous = answers
                finally:
                    c.close()

    def test_misrouting_is_rejected(self):
        model, sql, ddl, _, _ = study.read_inputs(ROOT)
        db = study.database(32)
        c = study.connect("sqlite", ":memory:")
        try:
            study.load(c, ddl, db)
            answers = study.validate(c, db, model, sql)
            p = study.plan(model, "quotient_cache")
            p["states"][p["initial"]]["query"] = 2
            with self.assertRaisesRegex(AssertionError, "stale or misrouted"):
                study.requests(c, model, sql, p, "quotient_cache", 1, answers)
        finally:
            c.close()

    def test_null_illegal_fk_and_duplicate_key_rejected(self):
        model, sql, ddl, _, _ = study.read_inputs(ROOT)
        db = study.database(32)
        c = study.connect("sqlite", ":memory:")
        try:
            study.load(c, ddl, db)
            invalid = deepcopy(db)
            row = list(invalid["EMP"][0])
            row[3] = None
            invalid["EMP"][0] = tuple(row)
            with self.assertRaisesRegex(AssertionError, "NULL input"):
                study.validate(c, invalid, model, sql)
            for index, value, message in ((7, 99999, "FK"), (0, 2, "key")):
                invalid = deepcopy(db)
                row = list(invalid["EMP"][0])
                row[index] = value
                invalid["EMP"][0] = tuple(row)
                with self.assertRaisesRegex(ValueError, message):
                    study.validate(c, invalid, model, sql)
        finally:
            c.close()

    def test_both_native_no_null_replays(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                result = study.native_replay(ROOT, engine)
                self.assertEqual(result["legal_databases"], 64)
                self.assertEqual(result["query_executions"], 1024)
                self.assertEqual(result["sql_to_cq_set_comparisons"], 1024)
                self.assertEqual(result["null_input_cells_encoded"], 0)
                self.assertGreater(result["adapter_negative_control_mismatches"], 0)

    def test_complete_trial_cost_and_fresh_paths(self):
        for engine in ENGINES:
            with self.subTest(engine=engine), tempfile.TemporaryDirectory(dir=WORK) as directory:
                work = Path(directory)
                result = study.trial(ROOT, work, engine, "quotient_cache", 32, 1, 0, {})
                stages = ["input_s", "plan_s", "build_load_s", "query_s", "maintenance_s",
                          "validation_s", "checkpoint_close_s", "reopen_validate_s"]
                self.assertGreaterEqual(result["total_s"], sum(result[k] for k in stages))
                self.assertGreaterEqual(result["plan_s"], result["produce_s"] + result["verify_s"])
                self.assertEqual(sum(e["executions"] for e in result["epochs"]), 40)
                self.assertEqual([e["tuples"] for e in result["epochs"]], [48, 49, 49, 49, 48])
                self.assertGreater(result["file_bytes"], 0)
                with self.assertRaises(AssertionError):
                    study.run(ROOT, work, work)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True)
    args, rest = parser.parse_known_args()
    if not args.work.is_dir():
        parser.error("--work must name an existing scratch directory")
    WORK = args.work
    print("Native engines checked:", ", ".join(ENGINES), flush=True)
    if "duckdb" not in ENGINES:
        print("DuckDB unavailable: its optional checks were not executed", flush=True)
    unittest.main(argv=[sys.argv[0], *rest])
