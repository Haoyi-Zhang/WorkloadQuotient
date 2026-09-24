# Recorded results

This directory contains the complete frozen scientific outputs used by the manuscript and reproduction wrapper. Timing and RSS fields are volatile; all other scientific fields are compared exactly during reproduction.

## Top-level summaries

- `clean-reproduction.json` — latest complete reproduction summary: 246 files, 56 certificates, 42 tests, 103,007 conservative obligations, SQLite replay passed.
- `direct-command-checks.json` — direct verifier and producer results for cascade case 06, including deterministic certificate equality.
- `engine-status.json` — SQLite execution status and explicit DuckDB non-execution.
- `resource-accounting.json` — limits, measured final run, and accounting boundary.
- `pilot.json`, `image-pilot.json` — pre-lock pilot measurements retained as scientific provenance.
- `figure-data/cascade-size.csv` — six coordinates regenerated from the cascade table and consumed by the paper plot.

## Cascade

`cascade/` contains sixteen frozen quotient certificates and matching minimum witnesses, the exact family table, six depth-boundary formula probes, two exhaustive tiny-domain oracles, and sixteen rejected mutation records. The executed depths are one through six. Formula-only all-key probes at depths seven through eleven are not materialized above the 128-tuple cap.

## Graphs

`graphs/` contains eight base graph controls and twenty-four key-subset ablations. Every case retains its quotient certificate, all constant-respecting candidate partitions, accepted minimum legal image, and independent exhaustive coloring record. Across the campaign there are 3,960 partitions and 203 coloring assignments. The illegal adjacent-color fold is rejected. `nonunique-optimum.json` records two nonisomorphic size-nine optima.

## Public fragment

`public/` contains eight quotient certificates derived from sixteen unchanged SQLSolver Calcite statements, a case table, and the SQLite 3.46.1 replay. All public pairs are equivalent in both directions under the locked set-valued fragment and minimize to a singleton quotient. The engine control uses sixty-four deterministic legal `EMP`/`DEPT` databases and reports 1,024 query executions; bag and set results agree for every pair/database combination.

The separate `../inputs/public-screening.csv` retains the earlier JOB negative screen. It is not included in the positive public-case count.

## Logs

`logs/` contains the frozen command outputs corresponding to the final recorded campaigns. Reproduction writes fresh logs into its chosen output directory and does not overwrite these records.

These outputs are finite evidence. They do not by themselves prove the general theorems, establish external review, or imply performance, optimizer, or general-SQL claims.
