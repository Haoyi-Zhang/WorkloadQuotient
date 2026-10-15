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

## Native snapshot study

`native-study/` is separate from the frozen five-stage results. `workload.json`
and `certificate.json` contain the composed sixteen-state public-query
workload, its eight-state quotient and 28 cross-block separators.
`trials.jsonl` contains all 120 complete lifecycle trials; `summary.json`
contains the forty condition medians/ranges, actual environment versions and
both 64-database no-NULL native replay records. See `../NATIVE-STUDY.md` for
the data, five runners, update schedule, cost accounting and commands.

The native study preserves unfavorable and near-equal outcomes. Quotient-block
caching has more cache keys than current-output caching, and reducing routing
states alone does not reduce the latter's native SQL executions. Database
tuples are identical across runners. Loaded native data are not generated
countermodels governed by the 128-tuple witness cap. These generated, warm
snapshot measurements do not establish production or general optimizer gains.

## Logs

`logs/` contains the frozen command outputs corresponding to the final recorded campaigns. Reproduction writes fresh logs into its chosen output directory and does not overwrite these records.

These outputs are finite evidence. They do not by themselves prove the general theorems or establish external review. Native cost results apply to the stated workload and protocol, not to general performance, optimizer behavior, or SQL semantics.
