# Public SQL screening, adapters, and provenance

## Frozen positive source

The positive public cases come from the Apache-2.0 `calcite_tests` file in the public SQLSolver repository at commit `dcc2a91d8971a4c4d30b055f99d7d8428a1b754b`. The source path is `sqlsolver_data/calcite/calcite_tests`; the accompanying key/foreign-key schema is `sqlsolver_data/schemas/calcite_test.base.schema.sql` at the same commit. License and attribution are retained under `third_party/sqlsolver/` and summarized in `THIRD-PARTY-NOTICES.md`.

The source file stores one SQL statement per physical line and pairs consecutive lines. Source-line numbers in this artifact are zero-based. `inputs/public-screening.csv` records all 181 consecutive pairs from lines 0--361. The frozen rule scans in ascending source order and admits the first eight pairs whose two statements can be represented, without deleting an SQL operator or condition, by the locked equality-only set-SPJ fragment over the published `EMP`/`DEPT` schema. Alias renaming, duplicate equality guards, and flattening a projection/selection-only derived table are permitted. Both retained CQs must be alpha-acyclic.

## Retained positive evidence and hand-written adapters

`manifest.json` freezes the repository, commit, path, selection rule, selected lines, admission reason, and exact SQL strings. `sqlsolver-selected.sql` preserves all 16 admitted statements unchanged except for terminating semicolons and provenance comments. Every `cases/public-XX.json` file retains the same SQL strings and line numbers next to an explicit finite CQ.

Those CQs are **hand-written adapters**. The executable artifact does not contain a general SQL parser or a verified SQL-to-CQ compiler. `adapter-contracts.json` and `ADAPTER-CONTRACTS.md` record, for every side of every pair, the table/column order, projection, equality predicates, SQL output types, nullable columns, and exact executable CQ. Unit tests require the manifest, contract, and case files to agree exactly.

SQLite executes the unchanged SQL on 64 deterministic legal databases. Separately, the checker evaluates every hand-written CQ after an explicit integer encoding of the same database and compares deduplicated result sets side by side. SQL integers are preserved; text values are mapped injectively to disjoint integers. Each SQL `NULL` input cell receives a different fresh integer, and no selected output may be `NULL`. This is only a finite control for these adapters: the paper's theory remains an integer domain without `NULL` and makes no general SQL-null claim. The retained run performs 1,024 SQL executions and 1,024 SQL-set/CQ-set comparisons. A deliberately corrupted P1 adapter that projects `JOB` instead of `ENAME` must disagree on at least one database.

## Exclusions and audit boundary

The 173 non-admitted SQLSolver rows use a conservative recorded decision: a pair is outside the locked fragment or appears after the eighth admission. They are not presented as 173 individually proved semantic diagnoses. Re-running the complete sequential source scan requires reacquiring the pinned Apache-2.0 source file; the retained manifest, selected SQL, adapters, and screening table remain auditable offline.

The Join Order Benchmark screen is separate and is stored under `inputs/job-negative/`, not in `inputs/public-screening.csv`. JOB queries `1a`--`1d` and `2a`--`2d` each contain `MIN`, so all eight are excluded unchanged. The JOB mirror has no declared repository license at the pinned commit; consequently the artifact retains immutable commit/blob identifiers and minimal excerpts but not the complete query files. No aggregate was deleted and no rewritten JOB query was substituted.
