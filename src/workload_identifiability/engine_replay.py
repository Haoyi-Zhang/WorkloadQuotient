"""Result replay for the eight pinned public SQL pairs.

The generated databases satisfy the upstream primary-key/foreign-key schema.
The theoretical paper uses set semantics; this replay checks both SQL bags and
set-deduplicated results.  DuckDB is used when requested and installed.  SQLite
is an independent built-in control, never relabeled as DuckDB.
"""
from __future__ import annotations
import argparse
from collections import Counter
import importlib
import json
from pathlib import Path
import random
import sqlite3
from typing import Any


def datasets(count: int = 64, seed: int = 20260918):
    rng = random.Random(seed)
    # Deterministic boundary cases first.
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


def _run_connection(connection, ddl: str, pairs: list[dict[str, Any]], dbs) -> dict:
    pair_stats = {p["id"]: {"databases": 0, "bag_equal": 0, "set_equal": 0,
                                  "max_bag_rows": 0, "max_set_rows": 0} for p in pairs}
    executions = 0
    for db in dbs:
        for statement in ddl.split(";"):
            if statement.strip(): connection.execute(statement)
        if isinstance(connection, sqlite3.Connection): connection.execute("PRAGMA foreign_keys=ON")
        if db["DEPT"]:
            connection.executemany("INSERT INTO DEPT VALUES (?, ?)", db["DEPT"])
        if db["EMP"]:
            connection.executemany("INSERT INTO EMP VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", db["EMP"])
        for pair in pairs:
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
                raise AssertionError(f"set-result mismatch in {pair['id']}")
            # These selected cases are also bag-equivalent under the declared keys.
            if not bag_equal:
                raise AssertionError(f"bag-result mismatch in {pair['id']}")
        connection.execute("DROP TABLE EMP")
        connection.execute("DROP TABLE DEPT")
    return {"pair_statistics": pair_stats, "query_executions": executions}


def replay(root: Path, output: Path, engine: str) -> dict:
    manifest = json.loads((root / "inputs/public/manifest.json").read_text(encoding="utf-8"))
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
        details = _run_connection(connection, ddl, manifest["pairs"], dbs)
    finally:
        connection.close()
    result = {
        "status": "ENGINE_REPLAY_PASSED",
        "engine": engine,
        "engine_version": version,
        "seed": 20260918,
        "legal_databases": len(dbs),
        "public_pairs": len(manifest["pairs"]),
        "all_set_results_equal": True,
        "all_bag_results_equal": True,
        "scope": "Deterministic generated legal Calcite EMP/DEPT databases; result equality only, no latency or optimizer claim.",
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
    except (AssertionError, RuntimeError, ValueError, sqlite3.DatabaseError) as error:
        print(json.dumps({"status": "NOT_COMPLETED", "engine": args.engine, "reason": str(error)}, indent=2))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
