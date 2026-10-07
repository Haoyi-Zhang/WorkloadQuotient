#!/usr/bin/env python3
"""Recreate every bounded finite result in this standalone repository.

The command produces five independent stage logs from one Linux run: regression
checks, cascades, graphs, public CQ certificates, and SQLite SQL/CQ replay.
Successful execution is finite evidence only, not a mechanized general proof or
an independent novelty review.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from workload_identifiability.evidence_compare import (  # noqa: E402
    ENVIRONMENT_FIELDS,
    VOLATILE_FIELDS,
    compare_tree,
    read_value,
    scientific_view,
)

EXPECTED_REGRESSION_TESTS = 54


def current_swap_kib() -> int:
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmSwap:"):
            return int(line.split()[1])
    raise RuntimeError("Cannot inspect process swap for the resource contract")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new, nonexistent directory")
    args = parser.parse_args()
    out = args.output.expanduser().absolute()
    if out.exists():
        parser.error("output already exists; choose a new directory")
    if not sys.platform.startswith("linux") or not hasattr(os, "sched_getaffinity"):
        parser.error("the complete resource-limited reproduction command requires Linux")
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (int(2.5 * 1024**3), int(2.5 * 1024**3)))
    resource.setrlimit(resource.RLIMIT_CPU, (240, 240))
    signal.signal(signal.SIGALRM, lambda signum, frame: (_ for _ in ()).throw(
        TimeoutError("300-second reproduction ceiling")))
    signal.alarm(300)
    out.mkdir(parents=True, exist_ok=False)
    (out / "logs").mkdir()
    wall = time.monotonic()
    self_cpu = time.process_time()
    before_child = resource.getrusage(resource.RUSAGE_CHILDREN)
    records = []
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0")

    def run(label: str, arguments: list[str]) -> None:
        started = time.monotonic()
        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        log = out / "logs" / (label + ".txt")
        with log.open("x", encoding="utf-8") as handle:
            result = subprocess.run(
                [sys.executable, *arguments],
                cwd=ROOT,
                env=env,
                stdout=handle,
                stderr=subprocess.STDOUT,
                timeout=300,
                check=False,
            )
        now = resource.getrusage(resource.RUSAGE_CHILDREN)
        records.append({
            "command": label,
            "returncode": result.returncode,
            "cpu_seconds": now.ru_utime + now.ru_stime - usage.ru_utime - usage.ru_stime,
            "wall_seconds": time.monotonic() - started,
            "log": str(log.relative_to(out)),
        })
        if result.returncode != 0:
            raise RuntimeError(f"{label} did not complete successfully; inspect {log}")

    try:
        run("regression-tests", ["-m", "unittest", "discover", "-s", "tests", "-v"])
        test_log = (out / "logs/regression-tests.txt").read_text(encoding="utf-8")
        if f"Ran {EXPECTED_REGRESSION_TESTS} tests" not in test_log or not test_log.rstrip().endswith("OK"):
            raise AssertionError("Unexpected regression test count or completion")
        run("cascade", ["-m", "workload_identifiability", "reproduce", "--output", str(out / "cascade")])
        run("graphs", ["-m", "workload_identifiability", "graphs", "--output", str(out / "graphs")])
        run("public-certificates", ["-m", "workload_identifiability", "public", "--output", str(out / "public")])
        run("sqlite-replay", [
            "-m", "workload_identifiability.engine_replay", "--root", str(ROOT),
            "--output", str(out / "public/sqlite-replay.json"), "--engine", "sqlite",
        ])

        files_compared = 0
        environment_drift: list[dict] = []
        for kind in ("cascade", "graphs"):
            for part in ("inputs", "results"):
                count, drift = compare_tree(ROOT / part / kind, out / kind / part)
                files_compared += count
                environment_drift.extend({"tree": f"{part}/{kind}", **item} for item in drift)
        count, drift = compare_tree(ROOT / "results/public", out / "public")
        files_compared += count
        environment_drift.extend({"tree": "results/public", **item} for item in drift)

        # Replay the independently implemented verifier over all frozen records.
        from workload_identifiability.verify import verify
        certificate_count = 0
        for path in sorted((ROOT / "inputs/cascade/families").glob("*.json")):
            verify(json.loads(path.read_text()), json.loads((ROOT / "results/cascade/certificates" / path.name).read_text()))
            certificate_count += 1
        for path in sorted((ROOT / "inputs/graphs").glob("*.json")):
            verify(json.loads(path.read_text()), json.loads((ROOT / "results/graphs/certificates" / path.name).read_text()))
            certificate_count += 1
        for path in sorted((ROOT / "inputs/public/cases").glob("*.json")):
            verify(json.loads(path.read_text()), json.loads((ROOT / "results/public/certificates" / path.name).read_text()))
            certificate_count += 1
        if certificate_count != 56:
            raise AssertionError("The frozen 56 generated/public certificates were not all replayed")

        with (out / "cascade/results/families.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        coordinates = []
        for depth in range(1, 7):
            all_keys = next(r for r in rows if int(r["depth"]) == depth and r["category"] == "all-identifier-keys")
            no_keys = next(r for r in rows if int(r["depth"]) == depth and r["category"] == "no-nonroot-identifier-keys")
            coordinates.append({
                "depth": str(depth),
                "canonical": all_keys["largest_canonical_witness"],
                "minimum_no_identifier": no_keys["minimum_witness"],
            })
        plot_file = out / "cascade-size.csv"
        with plot_file.open("x", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=coordinates[0])
            writer.writeheader()
            writer.writerows(coordinates)
        if scientific_view(read_value(plot_file)) != scientific_view(read_value(ROOT / "results/figure-data/cascade-size.csv")):
            raise AssertionError("The recorded plot data do not match the reproduced cascade table")

        cascade = json.loads((out / "cascade/results/campaign.json").read_text())
        graphs = json.loads((out / "graphs/results/graph-campaign.json").read_text())
        public = json.loads((out / "public/campaign.json").read_text())
        sqlite = json.loads((out / "public/sqlite-replay.json").read_text())
        semantic_totals = {
            "regression_test_methods": EXPECTED_REGRESSION_TESTS,
            "cascade_cases": cascade["families"],
            "base_graph_controls": graphs["graph_families"],
            "key_ablation_instances": graphs["key_ablation_instances"],
            "public_sql_pairs": public["cases"],
            "unchanged_public_sql_queries": public["unchanged_sql_queries"],
            "hand_written_cq_adapters": public["hand_written_cq_adapters"],
            "frozen_certificates_rechecked": certificate_count,
            "family_directed_containment_entries": cascade["directed_family_containment_checks"] + graphs["directed_containment_checks"],
            "public_directed_containment_entries": public["directed_containment_entries"],
            "family_block_pair_separators": cascade["family_separator_checks"] + graphs["separator_checks"],
            "public_block_pair_separators": public["block_pair_separators"],
            "tiny_legal_valuations": cascade["tiny_legal_valuations"],
            "tiny_query_evaluations": cascade["tiny_query_evaluations"],
            "image_partitions": graphs["image_partitions"],
            "coloring_assignments": graphs["coloring_assignments"],
            "sqlite_legal_databases": sqlite["legal_databases"],
            "sqlite_query_executions": sqlite["query_executions"],
            "sqlite_sql_to_cq_set_comparisons": sqlite["sql_to_cq_set_comparisons"],
            "sqlite_cq_adapter_evaluations": sqlite["cq_adapter_evaluations"],
            "adapter_negative_control_evaluations": sqlite["adapter_negative_control_evaluations"],
            "adapter_negative_control_mismatches": sqlite["adapter_negative_control_mismatches"],
            "sql_null_input_cells_finitely_encoded": sqlite["null_input_cells_encoded"],
            "producer_charged_search_obligations": cascade["producer_charged_search_obligations"] + graphs["producer_charged_search_obligations"],
            "mutated_certificates_rejected": cascade["mutations_rejected"],
            "illegal_graph_folds_rejected": graphs["adjacent_color_mutations_rejected"],
            "nonisomorphic_minimum_databases": graphs["nonisomorphic_optima"],
            "figure_rows_rebuilt": len(coordinates),
        }
        obligation_components = {
            "producer_charged_search_obligations": semantic_totals["producer_charged_search_obligations"],
            "tiny_ordered_query_pair_checks_36_per_legal_database": 36 * semantic_totals["tiny_legal_valuations"],
            "image_partitions": semantic_totals["image_partitions"],
            "coloring_assignments": semantic_totals["coloring_assignments"],
            "family_directed_containment_entries": semantic_totals["family_directed_containment_entries"],
            "family_block_pair_separators": semantic_totals["family_block_pair_separators"],
            "public_directed_containment_entries": semantic_totals["public_directed_containment_entries"],
            "public_block_pair_separators": semantic_totals["public_block_pair_separators"],
            "sqlite_query_executions": semantic_totals["sqlite_query_executions"],
        }
        obligations = sum(obligation_components.values())
        if obligations > 500000 or cascade["tiny_legal_valuations"] > 100000:
            raise RuntimeError("aggregate reproduction enumeration ceiling exceeded")
        child = resource.getrusage(resource.RUSAGE_CHILDREN)
        usage = resource.getrusage(resource.RUSAGE_SELF)
        cpu = (
            time.process_time() - self_cpu + child.ru_utime + child.ru_stime
            - before_child.ru_utime - before_child.ru_stime
        )
        if cpu > 6 * 3600 or current_swap_kib() != 0:
            raise RuntimeError("resource contract exceeded")
        summary = {
            "status": "FINITE_REPRODUCTION_PASSED",
            "scientific_files_compared": files_compared,
            "all_scientific_results_equal": True,
            "comparison_policy": {
                "volatile_measurement_fields_ignored": sorted(VOLATILE_FIELDS),
                "environment_metadata_fields_reported_not_scientifically_compared": sorted(ENVIRONMENT_FIELDS),
                "all_other_fields": "exact comparison",
            },
            "environment_metadata_drift": environment_drift,
            "counts": semantic_totals,
            "conservative_main_reproduction_obligation_components": obligation_components,
            "conservative_main_reproduction_obligations": obligations,
            "not_included_in_main_obligation_counter": [
                "regression tests",
                "scientific file comparisons",
                "certificate rechecks",
                "certificate mutation rejections",
                "illegal graph-fold rejection",
                "SQL-to-CQ adapter comparisons",
                "adapter negative-control evaluations",
                "figure rows rebuilt",
            ],
            "commands": records,
            "cpu_seconds": cpu,
            "wall_seconds": time.monotonic() - wall,
            "parent_peak_rss_kib": usage.ru_maxrss,
            "largest_child_peak_rss_kib": child.ru_maxrss,
            "process_swap_kib": 0,
            "workers": 1,
            "sqlite_replay": "PASSED",
            "duckdb_replay": "NOT_RUN_THIS_CAMPAIGN",
            "scope": (
                "Finite code, exact generated evidence, public-fragment certificates, SQLite pair-internal replay, "
                "and finite per-side SQL-set/CQ-set comparisons.  This is not an external review, a SQL parser "
                "validation, a NULL-semantics result, or a mechanized general proof."
            ),
        }
        with (out / "reproduction.json").open("x", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2, sort_keys=True)
            handle.write("\n")
        signal.alarm(0)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except (AssertionError, OSError, ValueError, RuntimeError, subprocess.TimeoutExpired, MemoryError, TimeoutError) as error:
        print(json.dumps({"status": "NOT_COMPLETED", "reason": str(error)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
