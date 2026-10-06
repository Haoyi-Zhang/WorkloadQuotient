# Recorded results

This directory contains the frozen scientific outputs used by the manuscript and reproduction wrapper. Timing and RSS fields are volatile. `engine_version` is retained as environment metadata and reported separately; every other result field is compared exactly.

## Top-level summaries

- `clean-reproduction.json` — one actual five-stage reproduction summary: 246 files, 56 certificates, 46 tests, 103,007 explicitly itemized main obligations, SQLite replay and SQL--CQ adapter comparisons passed.
- `direct-command-checks.json` — direct verifier and producer results for cascade case 06, including deterministic certificate equality.
- `engine-status.json` — SQLite execution status and explicit DuckDB non-execution.
- `resource-accounting.json` — limits, measured final run, and accounting boundary.
- `pilot.json`, `image-pilot.json` — pre-lock pilot measurements retained as scientific provenance.
- `figure-data/cascade-size.csv` — six coordinates regenerated from the cascade table and consumed by the paper plot.

## Cascade

`cascade/` contains sixteen frozen quotient certificates and matching minimum witnesses, the exact family table, five depth-boundary formula probes, two exhaustive tiny-domain oracles, and sixteen rejected mutation records. The executed depths are one through six. Formula-only all-key probes at depths seven through eleven are not materialized above the 128-tuple cap.

## Graphs

`graphs/` contains eight base graph controls and twenty-four key-subset ablations. Every case retains its quotient certificate, all constant-respecting candidate partitions, accepted minimum legal image, and independent exhaustive coloring record. Across the campaign there are 3,960 partitions and 203 coloring assignments. The illegal adjacent-color fold is rejected. `nonunique-optimum.json` records two nonisomorphic size-nine optima.

## Public fragment

`public/` contains eight quotient certificates derived from sixteen unchanged SQLSolver Calcite statements, a case table, and the SQLite replay. All pairs are equivalent in both directions under the locked set-valued fragment and minimize to a singleton quotient. Over sixty-four deterministic legal `EMP`/`DEPT` databases, 1,024 SQL executions agree within each pair for bags and sets; 1,024 per-side set comparisons against the hand-written CQ adapters also agree. A corrupted adapter is detected. The recorded SQLite version is environment metadata, not a semantic equality field.

The independent JOB negative screen is under `../inputs/job-negative/`; `../inputs/public-screening.csv` is only the 181-pair SQLSolver positive-source screening table. JOB is not included in the positive public-case count.

## Logs

`logs/` contains the frozen command outputs corresponding to the final recorded campaigns. Reproduction writes fresh logs into its chosen output directory and does not overwrite these records.

These outputs are finite evidence. They do not by themselves prove the general theorems, establish external review, or imply performance, optimizer, or general-SQL claims.
