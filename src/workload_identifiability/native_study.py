"""Native set-result and complete-lifecycle study of the retained public SQL.

No SQL is rewritten. Database updates separate read-only snapshots; they are
not actions of the workload theorem. Run with a fresh output and work directory.
DuckDB is optional for the original artifact, but required by this study.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import importlib
import json
import os
from pathlib import Path
import platform
import sqlite3
import statistics
import sys
import time

from .core import produce
from .engine_replay import _run_connection, datasets
from .public_adapters import FiniteSQLToCQEncoding, load_models, validate_contract
from .verify import legal_database, verify

MODES = ("direct", "literal_cache", "quotient_cache", "output_cache", "quotient_output_cache")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def read_inputs(root):
    validate_contract(root)
    manifest = json.loads((root / "inputs/public/manifest.json").read_text(encoding="utf-8"))
    models = load_models(root)
    pairs = manifest["pairs"]
    schema = models[pairs[0]["id"]]["schema"]
    require(all(models[p["id"]]["schema"] == schema for p in pairs), "different schemas")
    # The existing phase/copy construction, with eight public-pair phases.
    model = {
        "schema": schema, "queries": [q for p in pairs for q in models[p["id"]]["queries"]],
        "alphabet": ["clone", "next"], "initial": 0,
        "states": [{"query": 2 * phase + bit,
                    "next": {"clone": 2 * phase + 1 - bit,
                             "next": 2 * ((phase + 1) % len(pairs)) + bit}}
                   for phase in range(len(pairs)) for bit in range(2)],
    }
    sql = [s for p in pairs for s in p["sql"]]
    ddl = (root / "inputs/public/calcite-emp-dept.sql").read_text(encoding="utf-8")
    # Strengthen nullable input columns for this no-NULL track only.
    ddl = ddl.replace("MGR INTEGER,", "MGR INTEGER NOT NULL,").replace(
        "SLACKER INTEGER)", "SLACKER INTEGER NOT NULL)")
    return model, sql, ddl, pairs, models


def plan(model, mode):
    require(mode in MODES, "unknown mode")
    result = {"produce_s": 0.0, "verify_s": 0.0}
    blocks = [[i] for i in range(len(model["states"]))]
    labels = list(range(len(model["queries"])))
    if mode in ("quotient_cache", "output_cache", "quotient_output_cache"):
        started = time.perf_counter()
        certificate = produce(model)
        result["produce_s"] = time.perf_counter() - started
        started = time.perf_counter()
        verify(model, certificate)
        result["verify_s"] = time.perf_counter() - started
        blocks = certificate["blocks"]
        c = certificate["containment"]
        labels = [min(j for j in range(len(labels))
                      if c[f"{i},{j}"] is not None and c[f"{j},{i}"] is not None)
                  for i in range(len(labels))]
    if mode in ("quotient_cache", "quotient_output_cache"):
        cls = {s: i for i, block in enumerate(blocks) for s in block}
        routing = [{"query": min(model["states"][s]["query"] for s in block),
                    "next": {a: cls[model["states"][block[0]]["next"][a]]
                             for a in model["alphabet"]}} for block in blocks]
        initial = cls[model["initial"]]
        keys = ([labels[s["query"]] for s in routing] if mode == "quotient_output_cache"
                else list(range(len(blocks))))
        if mode == "quotient_output_cache":
            for state in routing:
                state["query"] = labels[state["query"]]
    else:
        routing = deepcopy(model["states"])
        initial = model["initial"]
        keys = [labels[s["query"]] if mode == "output_cache" else s["query"] for s in routing]
        if mode == "output_cache":
            for state in routing:
                state["query"] = labels[state["query"]]
    return {**result, "states": routing, "initial": initial, "keys": keys,
            "cache_keys": len(set(keys)), "routing_states": len(routing)}


def database(size):
    require(size >= 16, "size must be at least 16")
    # Bounded fanout (eight employees/department) keeps the unchanged self-joins
    # meaningful without manufacturing quadratic output volume at larger sizes.
    departments = max(16, (size + 7) // 8)
    return {"DEPT": [(i + 1, f"d{i + 1}") for i in range(departments)],
            "EMP": [(i + 1, f"e{i % 31}", f"j{i % 3}", 10 if i % 4 == 0 else 11,
                     1000 + i, 100 + i % 500, i % 50, i % departments + 1, i % 2)
                    for i in range(size)]}


def connect(engine, path):
    require(engine in ("sqlite", "duckdb"), "unknown engine")
    if engine == "sqlite":
        c = sqlite3.connect(str(path), isolation_level=None)
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA synchronous=FULL")
        c.execute("PRAGMA journal_mode=DELETE")
        c.execute("PRAGMA threads=1")
        return c
    return importlib.import_module("duckdb").connect(str(path), config={"threads": 1})


def load(c, ddl, db):
    c.execute("BEGIN TRANSACTION")
    for statement in ddl.split(";"):
        if statement.strip():
            c.execute(statement)
    for relation, placeholders in (("DEPT", "?, ?"), ("EMP", "?, ?, ?, ?, ?, ?, ?, ?, ?")):
        if db[relation]:
            c.executemany(f"INSERT INTO {relation} VALUES ({placeholders})", db[relation])
    c.execute("COMMIT")


def update(c, db, epoch):
    """Four fixed transactions: insert, rename, reassign/filter, delete."""
    c.execute("BEGIN TRANSACTION")
    if epoch == 1:
        key = max(row[0] for row in db["EMP"]) + 1
        row = (key, "inserted", "j0", 10, 9999, 200, 0, 10, 0)
        c.execute("INSERT INTO EMP VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
        db["EMP"].append(row)
    elif epoch == 2:
        c.execute("UPDATE DEPT SET NAME=? WHERE DEPTNO=?", ("renamed", 10))
        c.execute("UPDATE EMP SET ENAME=? WHERE EMPNO=?", ("renamed-e", 1))
        db["DEPT"] = [(k, "renamed" if k == 10 else name) for k, name in db["DEPT"]]
        db["EMP"] = [tuple("renamed-e" if j == 1 and row[0] == 1 else v
                           for j, v in enumerate(row)) for row in db["EMP"]]
    elif epoch == 3:
        c.execute("UPDATE EMP SET MGR=?", (11,))
        c.execute("UPDATE EMP SET DEPTNO=? WHERE EMPNO=?", (10, 2))
        db["EMP"] = [tuple(11 if j == 3 else 10 if row[0] == 2 and j == 7 else v
                           for j, v in enumerate(row)) for row in db["EMP"]]
    elif epoch == 4:
        key = max(row[0] for row in db["EMP"])
        c.execute("DELETE FROM EMP WHERE EMPNO=?", (key,))
        db["EMP"] = [row for row in db["EMP"] if row[0] != key]
    else:
        raise ValueError("unknown epoch")
    c.execute("COMMIT")


def validate(c, db, model, sql, expected=None):
    require(all(v is not None for rows in db.values() for row in rows for v in row), "NULL input")
    encoded = FiniteSQLToCQEncoding(db).cq_database()
    # This is a data-legality check, not a generated countermodel admission.
    legal_database(model["schema"], encoded, cap=sum(map(len, encoded.values())))
    for relation in db:
        require(set(map(tuple, c.execute(f"SELECT * FROM {relation}").fetchall())) == set(db[relation]),
                "stored data mismatch")
    answers = [frozenset(map(tuple, c.execute(s).fetchall())) for s in sql]
    for i in range(0, len(sql), 2):
        require(answers[i] == answers[i + 1], f"SQL pair mismatch {i // 2}")
    if expected is not None:
        require(answers == expected, "cross-engine/method/sweep/repetition result mismatch")
    return answers


def requests(c, model, sql, p, mode, sweeps, expected):
    cache = {}
    original = model["initial"]
    routed = p["initial"]
    executions = rows_fetched = maximum_cache_rows = 0
    actions = ["clone", "next"] * (len(sql) // 2) * sweeps
    for action in actions:
        key = p["keys"][routed]
        if mode == "direct" or key not in cache:
            raw = c.execute(sql[p["states"][routed]["query"]]).fetchall()
            rows_fetched += len(raw)
            answer = frozenset(map(tuple, raw))
            executions += 1
            if mode != "direct":
                cache[key] = answer
                maximum_cache_rows = max(maximum_cache_rows, sum(map(len, cache.values())))
        else:
            answer = cache[key]
        require(answer == expected[model["states"][original]["query"]], "stale or misrouted result")
        original = model["states"][original]["next"][action]
        routed = p["states"][routed]["next"][action]
    return {"requests": len(actions), "executions": executions, "rows_fetched": rows_fetched,
            "maximum_cache_answer_rows": maximum_cache_rows}


def trial(root, work, engine, mode, size, sweeps, repetition, reference):
    wall = time.perf_counter()
    cpu = time.process_time()
    started = time.perf_counter()
    model, sql, ddl, _, _ = read_inputs(root)
    db = database(size)
    input_s = time.perf_counter() - started
    started = time.perf_counter()
    p = plan(model, mode)
    plan_s = time.perf_counter() - started
    path = work / f"{engine}-{mode}-{size}-{sweeps}-{repetition}.db"
    started = time.perf_counter()
    c = connect(engine, path)
    load(c, ddl, db)
    build_load_s = time.perf_counter() - started
    validation_s = query_s = maintenance_s = 0.0
    epoch_records = []
    try:
        for epoch in range(5):
            if epoch:
                started = time.perf_counter()
                update(c, db, epoch)
                # The previous requests() call's snapshot-local cache is gone.
                maintenance_s += time.perf_counter() - started
            started = time.perf_counter()
            answers = validate(c, db, model, sql, reference.get((size, epoch)))
            reference.setdefault((size, epoch), answers)
            validation_s += time.perf_counter() - started
            started = time.perf_counter()
            counts = requests(c, model, sql, p, mode, sweeps, answers)
            query_s += time.perf_counter() - started
            epoch_records.append({"epoch": epoch, "tuples": sum(map(len, db.values())), **counts})
        # Validate the final stored data/results again, and flush before closing.
        started = time.perf_counter()
        validate(c, db, model, sql, reference[(size, 4)])
        validation_s += time.perf_counter() - started
    finally:
        started = time.perf_counter()
        if engine == "duckdb":
            c.execute("CHECKPOINT")
        c.close()
        close_s = time.perf_counter() - started
    started = time.perf_counter()
    reopened = connect(engine, path)
    try:
        validate(reopened, db, model, sql, reference[(size, 4)])
    finally:
        reopened.close()
    reopen_validate_s = time.perf_counter() - started
    file_bytes = path.stat().st_size
    total_s = time.perf_counter() - wall
    stages = {"input_s": input_s, "plan_s": plan_s, "build_load_s": build_load_s,
              "query_s": query_s, "maintenance_s": maintenance_s,
              "validation_s": validation_s, "checkpoint_close_s": close_s,
              "reopen_validate_s": reopen_validate_s}
    require(total_s >= sum(stages.values()), "incomplete total accounting")
    return {"engine": engine, "mode": mode, "employees": size, "sweeps": sweeps,
            "repetition": repetition, "routing_states": p["routing_states"],
            "cache_keys": p["cache_keys"], "produce_s": p["produce_s"], "verify_s": p["verify_s"],
            **stages, "unallocated_s": total_s - sum(stages.values()), "total_s": total_s,
            "cpu_s": time.process_time() - cpu, "file_bytes": file_bytes, "epochs": epoch_records}


def native_replay(root, engine):
    _, _, ddl, pairs, models = read_inputs(root)
    dbs = list(datasets())
    for db in dbs:
        db["EMP"] = [tuple(11 if v is None else v for v in row) for row in db["EMP"]]
    c = connect(engine, ":memory:")
    try:
        details = _run_connection(c, ddl, pairs, dbs, models)
    finally:
        c.close()
    return {"engine": engine, "legal_databases": len(dbs), "NULL_cells": 0, **details}


def summarize(records):
    rows = []
    groups = sorted({(r["engine"], r["employees"], r["sweeps"], r["mode"]) for r in records})
    stages = ("input_s", "plan_s", "produce_s", "verify_s", "build_load_s", "query_s",
              "maintenance_s", "validation_s", "checkpoint_close_s", "reopen_validate_s", "total_s", "cpu_s")
    for engine, size, sweeps, mode in groups:
        rr = [r for r in records if (r["engine"], r["employees"], r["sweeps"], r["mode"])
              == (engine, size, sweeps, mode)]
        rows.append({"engine": engine, "employees": size, "sweeps": sweeps, "mode": mode,
                     "repetitions": len(rr), "routing_states": rr[0]["routing_states"],
                     "cache_keys": rr[0]["cache_keys"],
                     "executions": sum(e["executions"] for e in rr[0]["epochs"]),
                     "requests": sum(e["requests"] for e in rr[0]["epochs"]),
                     "total_min_s": min(r["total_s"] for r in rr),
                     "total_max_s": max(r["total_s"] for r in rr),
                     "file_bytes_median": statistics.median(r["file_bytes"] for r in rr),
                     **{k + "_median": statistics.median(r[k] for r in rr) for k in stages}})
    return rows


def run(root, output, work, sizes=(128, 1024), sweep_counts=(1, 8), repetitions=3):
    require(not output.exists() and not work.exists(), "choose fresh output and work directories")
    output.mkdir(parents=True)
    work.mkdir(parents=True)
    duckdb = importlib.import_module("duckdb")
    model, _, _, _, _ = read_inputs(root)
    certificate = produce(model)
    checked = verify(model, certificate)
    (output / "workload.json").write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    (output / "certificate.json").write_text(json.dumps(certificate, indent=2) + "\n", encoding="utf-8")
    replay = [native_replay(root, e) for e in ("sqlite", "duckdb")]
    records, reference = [], {}
    # Rotated order; all methods run in one process on new file-backed databases.
    for size in sizes:
        for sweeps in sweep_counts:
            for rep in range(repetitions):
                modes = MODES[rep % len(MODES):] + MODES[:rep % len(MODES)]
                for mode in modes:
                    for engine in (("sqlite", "duckdb") if rep % 2 == 0 else ("duckdb", "sqlite")):
                        record = trial(root, work, engine, mode, size, sweeps, rep, reference)
                        records.append(record)
                        with (output / "trials.jsonl").open("a", encoding="utf-8") as handle:
                            handle.write(json.dumps(record, sort_keys=True) + "\n")
                        print(f"{len(records)} {engine} {mode} n={size} sweeps={sweeps} "
                              f"total={record['total_s']:.6f}s", flush=True)
    summary = {
        "status": "NATIVE_STUDY_PASSED", "python": sys.version, "os": platform.platform(),
        "machine": platform.machine(), "processor": platform.processor(),
        "logical_cpus": os.cpu_count(), "sqlite": sqlite3.sqlite_version, "duckdb": duckdb.__version__,
        "workers_per_engine": 1, "storage": "fresh file-backed databases; engine-default indexes",
        "sqlite_settings": {"foreign_keys": True, "synchronous": "FULL", "journal_mode": "DELETE"},
        "semantics": "unchanged SQL; fetch all bag rows, normalize to sets; no NULL inputs",
        "updates": ["insert EMP", "rename DEPT and EMP", "reassign EMP.DEPTNO; remove MGR=10 matches", "delete inserted EMP"],
        "invalidation": "discard every answer cache at snapshot boundaries before updates; schema certificate reused",
        "cost_boundary": "input/contract, proof production/check, routing/cache, database create/load/commit, "
                         "requests/fetch/set conversion/check, updates, all-SQL/data/legality validation, "
                         "checkpoint/close/reopen/final validation; total is outer wall time; import/install and study-wide replay separate",
        "same_information_baseline": "output_cache and quotient_output_cache are charged the identical full "
                                     "certificate production/check and cache by current-query equivalence; "
                                     "only their routing representation differs",
        "workload": checked, "native_replay": replay, "trials": len(records),
        "cross_engine_method_snapshot_sets_equal": True, "rows": summarize(records),
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--sizes", type=int, nargs="+", default=[128, 1024])
    parser.add_argument("--sweeps", type=int, nargs="+", default=[1, 8])
    parser.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args()
    require(args.repetitions > 0 and all(s > 0 for s in args.sweeps), "positive run dimensions required")
    result = run(args.root, args.output, args.work, tuple(args.sizes), tuple(args.sweeps), args.repetitions)
    print(json.dumps({"status": result["status"], "trials": result["trials"]}), flush=True)


if __name__ == "__main__":
    main()
