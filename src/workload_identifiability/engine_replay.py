"""Finite result replay for the eight pinned public SQL pairs.

The unchanged SQL is executed by the selected engine.  Separately, each
hand-written CQ adapter is evaluated over an explicit integer encoding of the
same finite database and compared with the corresponding deduplicated SQL
result.  This is not a SQL parser, a verified compiler, a NULL-semantics model,
or a universal equivalence proof.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import importlib
import json
from pathlib import Path
import random
import sqlite3
from typing import Any

from .public_adapters import FiniteSQLToCQEncoding, load_models, validate_contract
from .verify import evaluate, legal_database


def datasets(count: int = 64, seed: int = 20260918):
    rng = random.Random(seed)
    # Deterministic boundary cases first.  MGR=None is an SQL-side control;
    # the paper's CQ theory itself has no NULL value.
    yield {"DEPT": [], "EMP": []}
    yield {"DEPT": [(10, "d10")], "EMP": []}
    yield {"DEPT": [(10, "d10")], "EMP": [(1, "a", "j", 10, 1, 100, 0, 10, 0)]}
    yield {"DEPT": [(7, "d7"), (10, "d10")], "EMP": [
        (1, "a", "j", None, 1, 100, 0, 7, 0),
        (2, "b", "j", 10, 2, 200, 0, 7, 1),
        (3, "a", "k", 10, 3, 300, 0, 10, 0),
    ]}
    for case in range(count - 4):
        dept_ids = sorted(rng.sample([1, 2, 3, 7, 10, 20], rng.randrange(0, 5)))
        dept = [(d, f"d{d}") for d in dept_ids]
        emp = []
        if dept_ids:
            for j in range(rng.randrange(0, 9)):
                empno = case * 20 + j + 1
                dep = rng.choice(dept_ids)
                mgr = rng.choice([None, 10, 11, empno])
                emp.append((empno, f"e{rng.randrange(4)}", f"j{rng.randrange(3)}", mgr,
                            1000 + j, rng.randrange(0, 500), rng.randrange(0, 50), dep,
                            rng.randrange(0, 2)))
        yield {"DEPT": dept, "EMP": emp}


def _sort_rows(rows):
    return sorted((tuple(row) for row in rows), key=repr)


def _run_connection(
    connection,
    ddl: str,
    pairs: list[dict[str, Any]],
    dbs: list[dict[str, list[tuple[Any, ...]]]],
    models: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    pair_stats = {
        pair["id"]: {
            "databases": 0,
            "bag_equal": 0,
            "set_equal": 0,
            "left_sql_cq_set_equal": 0,
            "right_sql_cq_set_equal": 0,
            "max_bag_rows": 0,
            "max_set_rows": 0,
        }
        for pair in pairs
    }
    executions = 0
    adapter_comparisons = 0
    adapter_evaluations = 0
    negative_control_evaluations = 0
    negative_control_mismatches = 0
    null_cells_encoded = 0

    for database_index, db in enumerate(dbs):
        for statement in ddl.split(";"):
            if statement.strip():
                connection.execute(statement)
        if isinstance(connection, sqlite3.Connection):
            connection.execute("PRAGMA foreign_keys=ON")
        if db["DEPT"]:
            connection.executemany("INSERT INTO DEPT VALUES (?, ?)", db["DEPT"])
        if db["EMP"]:
            connection.executemany("INSERT INTO EMP VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", db["EMP"])

        encoding = FiniteSQLToCQEncoding(db)
        cq_database = encoding.cq_database()
        # All eight adapters share this schema.  This checks that the explicit
        # finite encoding preserves declared keys/FKs and remains in the
        # integer-only theory domain.
        legal_database(models[pairs[0]["id"]]["schema"], cq_database)
        null_cells_encoded += encoding.null_cells

        for pair in pairs:
            model = models[pair["id"]]
            left = _sort_rows(connection.execute(pair["sql"][0]).fetchall())
            right = _sort_rows(connection.execute(pair["sql"][1]).fetchall())
            executions += 2
            stats = pair_stats[pair["id"]]
            stats["databases"] += 1
            bag_equal = Counter(left) == Counter(right)
            set_equal = set(left) == set(right)
            stats["bag_equal"] += int(bag_equal)
            stats["set_equal"] += int(set_equal)
            stats["max_bag_rows"] = max(stats["max_bag_rows"], len(left), len(right))
            stats["max_set_rows"] = max(stats["max_set_rows"], len(set(left)), len(set(right)))
            if not set_equal:
                raise AssertionError(f"set-result mismatch in {pair['id']} database {database_index}")
            # These selected cases are also bag-equivalent under the declared keys.
            if not bag_equal:
                raise AssertionError(f"bag-result mismatch in {pair['id']} database {database_index}")

            sql_left_set = encoding.output_set(left)
            sql_right_set = encoding.output_set(right)
            cq_left_set = evaluate(model["queries"][0], cq_database)
            cq_right_set = evaluate(model["queries"][1], cq_database)
            adapter_evaluations += 2
            adapter_comparisons += 2
            left_equal = sql_left_set == cq_left_set
            right_equal = sql_right_set == cq_right_set
            stats["left_sql_cq_set_equal"] += int(left_equal)
            stats["right_sql_cq_set_equal"] += int(right_equal)
            if not left_equal:
                raise AssertionError(
                    f"SQL/CQ adapter mismatch in {pair['id']} left side, database {database_index}: "
                    f"sql={sorted(sql_left_set)!r}, cq={sorted(cq_left_set)!r}"
                )
            if not right_equal:
                raise AssertionError(
                    f"SQL/CQ adapter mismatch in {pair['id']} right side, database {database_index}: "
                    f"sql={sorted(sql_right_set)!r}, cq={sorted(cq_right_set)!r}"
                )

            # Negative control: public-01's left adapter deliberately projects
            # JOB instead of ENAME.  At least one retained database must expose
            # the error; otherwise the cross-path check is non-discriminating.
            if pair["id"] == "public-01":
                corrupted = deepcopy(model["queries"][0])
                corrupted["head"] = ["v:e2"]
                corrupted_set = evaluate(corrupted, cq_database)
                negative_control_evaluations += 1
                if corrupted_set != sql_left_set:
                    negative_control_mismatches += 1

        connection.execute("DROP TABLE EMP")
        connection.execute("DROP TABLE DEPT")

    if negative_control_mismatches == 0:
        raise AssertionError("corrupted public-01 adapter was not detected")
    return {
        "pair_statistics": pair_stats,
        "query_executions": executions,
        "sql_to_cq_set_comparisons": adapter_comparisons,
        "cq_adapter_evaluations": adapter_evaluations,
        "adapter_negative_control_evaluations": negative_control_evaluations,
        "adapter_negative_control_mismatches": negative_control_mismatches,
        "null_input_cells_encoded": null_cells_encoded,
    }


def replay(root: Path, output: Path, engine: str) -> dict[str, Any]:
    manifest = json.loads((root / "inputs/public/manifest.json").read_text(encoding="utf-8"))
    validate_contract(root)
    models = load_models(root)
    ddl = (root / "inputs/public/calcite-emp-dept.sql").read_text(encoding="utf-8")
    dbs = list(datasets())
    if engine == "sqlite":
        connection = sqlite3.connect(":memory:")
        connection.execute("PRAGMA foreign_keys=ON")
        version = sqlite3.sqlite_version
    elif engine == "duckdb":
        try:
            duckdb = importlib.import_module("duckdb")
        except ModuleNotFoundError as error:
            raise RuntimeError("DuckDB Python package is not installed; replay not executed") from error
        connection = duckdb.connect(database=":memory:")
        version = duckdb.__version__
    else:
        raise ValueError("engine must be sqlite or duckdb")
    try:
        details = _run_connection(connection, ddl, manifest["pairs"], dbs, models)
    finally:
        connection.close()
    expected_adapter_comparisons = len(dbs) * len(manifest["pairs"]) * 2
    if details["sql_to_cq_set_comparisons"] != expected_adapter_comparisons:
        raise AssertionError("not every SQL side was compared with its CQ adapter")
    result = {
        "status": "ENGINE_REPLAY_PASSED",
        "engine": engine,
        "engine_version": version,
        "engine_version_role": (
            "environment metadata only; exact semantic fields are compared independently of this string"
        ),
        "seed": 20260918,
        "legal_databases": len(dbs),
        "public_pairs": len(manifest["pairs"]),
        "hand_written_cq_adapters": len(models),
        "all_set_results_equal_within_sql_pairs": True,
        "all_bag_results_equal_within_sql_pairs": True,
        "all_sql_to_cq_set_results_equal": True,
        "adapter_error_negative_control_rejected": True,
        "theory_null_semantics_claim": False,
        "finite_encoding": {
            "integers": "preserved exactly",
            "text": "injective integers disjoint from SQL integer values within each database",
            "null": "each input NULL cell receives a fresh ordinary integer; selected outputs may not contain NULL",
        },
        "scope": (
            "Sixty-four deterministic legal Calcite EMP/DEPT databases.  SQL pair-internal set/bag equality and "
            "per-side SQL-set versus hand-written-CQ-set equality are finite checks only; no parser, compiler, "
            "general SQL, NULL-semantics, latency, or optimizer claim."
        ),
        **details,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--engine", choices=("sqlite", "duckdb"), required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(replay(args.root, args.output, args.engine), indent=2, sort_keys=True))
        return 0
    except (AssertionError, RuntimeError, ValueError, TypeError, sqlite3.DatabaseError) as error:
        print(json.dumps({"status": "NOT_COMPLETED", "engine": args.engine, "reason": str(error)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
