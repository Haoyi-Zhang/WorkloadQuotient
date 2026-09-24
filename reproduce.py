#!/usr/bin/env python3
"""Recreate every bounded finite result in this standalone repository.

The complete command uses only Python's standard library and the files shipped
in the repository.  It rebuilds generated families, graph instances, public
fragment certificates, and the SQLite result-equality control.  DuckDB replay is
implemented separately and is reported only when that package is actually
installed; it is never inferred from the SQLite run.
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
VOLATILE = {"cpu_seconds", "wall_seconds", "peak_rss_kib"}


def normalized(value):
    """Remove only explicitly named resource measurements, recursively."""
    if isinstance(value, dict):
        return {k: normalized(v) for k, v in value.items() if k not in VOLATILE}
    if isinstance(value, list):
        return [normalized(v) for v in value]
    return value


def read_scientific(path: Path):
    if path.suffix == ".json":
        return normalized(json.loads(path.read_text(encoding="utf-8")))
    if path.suffix == ".jsonl":
        return [normalized(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines()]
    if path.suffix == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            return [normalized(row) for row in csv.DictReader(handle)]
    return path.read_bytes()


def compare_tree(expected: Path, actual: Path) -> int:
    left = {p.relative_to(expected) for p in expected.rglob("*") if p.is_file()}
    right = {p.relative_to(actual) for p in actual.rglob("*") if p.is_file()}
    if left != right:
        raise AssertionError(f"Different evidence files: missing={sorted(left-right)}, extra={sorted(right-left)}")
    for rel in sorted(left):
        if read_scientific(expected / rel) != read_scientific(actual / rel):
            raise AssertionError(f"Scientific evidence differs: {expected.name}/{rel}")
    return len(left)


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

    def run(label: str, arguments: list[str]):
        started = time.monotonic()
        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        log = out / "logs" / (label + ".txt")
        with log.open("x", encoding="utf-8") as handle:
            result = subprocess.run([sys.executable, *arguments], cwd=ROOT, env=env,
                                    stdout=handle, stderr=subprocess.STDOUT,
                                    timeout=300, check=False)
        now = resource.getrusage(resource.RUSAGE_CHILDREN)
        records.append({"command": label, "returncode": result.returncode,
                        "cpu_seconds": now.ru_utime + now.ru_stime - usage.ru_utime - usage.ru_stime,
                        "wall_seconds": time.monotonic() - started,
                        "log": str(log.relative_to(out))})
        if result.returncode != 0:
            raise RuntimeError(f"{label} did not complete successfully; inspect {log}")

    try:
        run("regression-tests", ["-m", "unittest", "discover", "-s", "tests", "-v"])
        test_log = (out / "logs/regression-tests.txt").read_text(encoding="utf-8")
        if "Ran 42 tests" not in test_log or not test_log.rstrip().endswith("OK"):
            raise AssertionError("Unexpected regression test count or completion")
        run("cascade", ["-m", "workload_identifiability", "reproduce", "--output", str(out / "cascade")])
        run("graphs", ["-m", "workload_identifiability", "graphs", "--output", str(out / "graphs")])
        run("public-certificates", ["-m", "workload_identifiability", "public", "--output", str(out / "public")])
        run("sqlite-replay", ["-m", "workload_identifiability.engine_replay", "--root", str(ROOT),
                              "--output", str(out / "public/sqlite-replay.json"), "--engine", "sqlite"])

        files_compared = 0
        for kind in ("cascade", "graphs"):
            for part in ("inputs", "results"):
                files_compared += compare_tree(ROOT / part / kind, out / kind / part)
        files_compared += compare_tree(ROOT / "results/public", out / "public")

        # Replay the independently implemented verifier over all frozen records.
        sys.path.insert(0, str(ROOT / "src"))
        from workload_identifiability.verify import verify
        count = 0
        for path in sorted((ROOT / "inputs/cascade/families").glob("*.json")):
            verify(json.loads(path.read_text()), json.loads((ROOT / "results/cascade/certificates" / path.name).read_text()))
            count += 1
        for path in sorted((ROOT / "inputs/graphs").glob("*.json")):
            verify(json.loads(path.read_text()), json.loads((ROOT / "results/graphs/certificates" / path.name).read_text()))
            count += 1
        for path in sorted((ROOT / "inputs/public/cases").glob("*.json")):
            verify(json.loads(path.read_text()), json.loads((ROOT / "results/public/certificates" / path.name).read_text()))
            count += 1
        if count != 56:
            raise AssertionError("The frozen 56 generated/public certificates were not all replayed")

        with (out / "cascade/results/families.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        coordinates = []
        for depth in range(1, 7):
            all_keys = next(r for r in rows if int(r["depth"]) == depth and r["category"] == "all-identifier-keys")
            no_keys = next(r for r in rows if int(r["depth"]) == depth and r["category"] == "no-nonroot-identifier-keys")
            coordinates.append({"depth": str(depth), "canonical": all_keys["largest_canonical_witness"],
                                "minimum_no_identifier": no_keys["minimum_witness"]})
        plot_file = out / "cascade-size.csv"
        with plot_file.open("x", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=coordinates[0]); writer.writeheader(); writer.writerows(coordinates)
        if read_scientific(plot_file) != read_scientific(ROOT / "results/figure-data/cascade-size.csv"):
            raise AssertionError("The recorded plot data do not match the reproduced cascade table")

        cascade = json.loads((out / "cascade/results/campaign.json").read_text())
        graphs = json.loads((out / "graphs/results/graph-campaign.json").read_text())
        public = json.loads((out / "public/campaign.json").read_text())
        sqlite = json.loads((out / "public/sqlite-replay.json").read_text())
        semantic_totals = {
            "regression_test_methods": 42,
            "cascade_cases": cascade["families"],
            "base_graph_controls": graphs["graph_families"],
            "key_ablation_instances": graphs["key_ablation_instances"],
            "public_sql_pairs": public["cases"],
            "unchanged_public_sql_queries": public["unchanged_sql_queries"],
            "frozen_certificates_rechecked": count,
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
            "producer_charged_search_obligations": cascade["producer_charged_search_obligations"] + graphs["producer_charged_search_obligations"],
            "mutated_certificates_rejected": cascade["mutations_rejected"],
            "illegal_graph_folds_rejected": graphs["adjacent_color_mutations_rejected"],
            "nonisomorphic_minimum_databases": graphs["nonisomorphic_optima"],
            "figure_rows_rebuilt": len(coordinates),
        }
        obligations = (semantic_totals["producer_charged_search_obligations"]
                       + 36 * semantic_totals["tiny_legal_valuations"]
                       + semantic_totals["image_partitions"] + semantic_totals["coloring_assignments"]
                       + semantic_totals["family_directed_containment_entries"]
                       + semantic_totals["family_block_pair_separators"]
                       + semantic_totals["public_directed_containment_entries"]
                       + semantic_totals["public_block_pair_separators"]
                       + semantic_totals["sqlite_query_executions"])
        if obligations > 500000 or cascade["tiny_legal_valuations"] > 100000:
            raise RuntimeError("aggregate reproduction enumeration ceiling exceeded")
        child = resource.getrusage(resource.RUSAGE_CHILDREN)
        usage = resource.getrusage(resource.RUSAGE_SELF)
        cpu = (time.process_time() - self_cpu + child.ru_utime + child.ru_stime
               - before_child.ru_utime - before_child.ru_stime)
        if cpu > 6 * 3600 or current_swap_kib() != 0:
            raise RuntimeError("resource contract exceeded")
        summary = {
            "status": "FINITE_REPRODUCTION_PASSED",
            "scientific_files_compared": files_compared,
            "all_scientific_results_equal": True,
            "comparison_excludes_only": sorted(VOLATILE),
            "counts": semantic_totals,
            "conservative_main_reproduction_obligations": obligations,
            "commands": records,
            "cpu_seconds": cpu,
            "wall_seconds": time.monotonic() - wall,
            "parent_peak_rss_kib": usage.ru_maxrss,
            "largest_child_peak_rss_kib": child.ru_maxrss,
            "process_swap_kib": 0,
            "workers": 1,
            "sqlite_replay": "PASSED",
            "duckdb_replay": "NOT_RUN_PACKAGE_UNAVAILABLE",
            "scope": ("Finite code, exact generated evidence, public-fragment certificates, and an independent "
                      "SQLite result-equality control; not an external review or a mechanized general proof."),
        }
        with (out / "reproduction.json").open("x", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2, sort_keys=True); handle.write("\n")
        signal.alarm(0)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except (AssertionError, OSError, ValueError, RuntimeError, subprocess.TimeoutExpired, MemoryError) as error:
        print(json.dumps({"status": "NOT_COMPLETED", "reason": str(error)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
