# Workload Identifiability

This standalone repository contains the implementation, proof notes, frozen inputs, certificates, raw finite results, and provenance ledgers for **Canonical Workload Quotients and the Cost of Distinguishing Databases**. It is complete for the locked internal research scope. The paper's general statements are mathematical theorems; the programs perform finite generation, replay, mutation testing, and independent certificate checks. Successful execution is not a machine-checked proof or independent peer review.

## Result and scope

The model compares ordered traces of set-valued equality conjunctive-query answers on the same legal database. Admitted queries are alpha-acyclic; the relation-level foreign-key graph is independently required to be acyclic; each foreign key targets a declared key. Constants are rigid canonical integers. The workload has a finite concrete action alphabet.

The repository supports these paper claims:

- finite universal source instances and exact containment in the locked dependency class;
- a canonical coarsest reachable workload congruence and unique state-minimum quotient;
- minimum directed countermodels as legal homomorphic images of the source instance;
- an exact key-sensitive cascade with four quotient states but linear or exponential minimum witnesses;
- an exact graph reduction with minimum `n - 1 + 2m + chromatic_number(G)` and NP-complete combined complexity; and
- a replayable certificate whose reachability, containment maps, partition, transition congruence, and actual separating databases are checked separately.

No general SQL, cyclic-dependency, null, update-transition, recursion, aggregate, inequality, disjunction, learned-model, natural-language, production-latency, deployment, or 128-tuple small-model claim is made. The optional native snapshot study measures a bounded lifecycle cost, with legal updates between read-only traces rather than update actions in the theorem. The latest small-counterexample literature is treated as prior existence theory; the delta here is exact legal-image minimization and its tight families/complexity.

## Full reproduction

Use Linux with Python 3.10 or newer. The complete wrapper uses `/proc/self/status`, CPU affinity, and POSIX resource limits; it does not run on macOS or native Windows. The reproduction uses only the Python standard library and requires no network access or package installation. Choose a new, nonexistent output directory:

```sh
python3 reproduce.py --output ../workload-reproduction
```

The command sequentially runs 54 regression tests, recreates the cascade, graph, public-certificate, and SQLite campaigns, compares 246 scientific files, replays all 56 certificates through the verifier, and rebuilds the cascade plot data. CPU time, wall time, and peak RSS are volatile measurements. `engine_version` is retained and reported as environment metadata but is not a scientific equality field; every other result field is compared exactly. A version-only fixture must pass with reported drift, while a changed semantic-result fixture must fail. The frozen Linux summary records the earlier 46-test run and the retained Ubuntu measurement covers 48 tests; neither is rewritten as a measurement of the expanded suite.

A successful `reproduction.json` is written only after every command and comparison succeeds. Existing output directories are never overwritten. A cap, timeout, or failure to construct a witness returns failure or `UNKNOWN`; it never certifies equivalence.

Component checks from the repository root:

```sh
python3 -m unittest discover -s tests -v
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m workload_identifiability check \
  inputs/cascade/families/case-06.json \
  results/cascade/certificates/case-06.json
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -m workload_identifiability produce \
  inputs/cascade/families/case-06.json \
  --output ../quotient-certificate.json
```

Exit code 0 is a successful finite check/generation; 1 is rejection or an I/O/input error; 2 is `UNKNOWN` at a declared bound. See `FORMAT.md` for the trusted-model and certificate boundary.

## Recorded evidence

| Evidence unit | Outcome | Location |
|---|---:|---|
| Cascade parameter cases | 16 | `results/cascade/families.csv` |
| Base graph controls | 8 | `results/graphs/graphs.csv` |
| Exhaustive graph key-ablation instances | 24 | `results/graphs/graphs.csv` |
| Public equality-SPJ pairs | 8 pairs / 16 unchanged SQL statements | `inputs/public/`, `results/public/` |
| Accepted quotient certificates | 56 | `results/*/certificates/` |
| Generated-family directed containment entries | 768 | campaign summaries |
| Public directed containment entries | 32 | `results/public/campaign.json` |
| Generated quotient block-pair separators | 288 | campaign summaries |
| Legal tiny-domain databases | 2,583 | `results/cascade/tiny-valuations.jsonl` |
| Tiny set-query evaluations | 15,498 | `results/cascade/tiny-oracle.json` |
| Constant-respecting image partitions | 3,960 | `results/graphs/partitions/` |
| Coloring assignments | 203 | `results/graphs/coloring-oracle/` |
| Obligation-breaking quotient mutations | 16/16 rejected | `results/cascade/mutations.json` |
| Additional illegal graph fold | rejected | `results/graphs/adjacent-color-mutation.json` |
| Nonisomorphic optimum databases | 2, both size 9 | `results/graphs/nonunique-optimum.json` |
| Regression tests | 54 in the main suite; 46 frozen / 48 retained Ubuntu | `tests/test_semantics.py`, `tests/test_family_boundaries.py`, `tests/test_match_rows.py` |
| Distinguishing-suffix regressions | 2 supplementary methods | `tests/regression_suffix_bound.py` |
| SQLite legal databases | 64 | `results/public/sqlite-replay.json` |
| SQLite query executions | 1,024 | `results/public/sqlite-replay.json` |
| SQLite-set to hand-written-CQ-set comparisons | 1,024, all equal | `results/public/sqlite-replay.json` |
| Corrupted-adapter negative control | 40/64 databases expose the error | `results/public/sqlite-replay.json` |
| Historical DuckDB status | not run on the original host | `results/engine-status.json` |
| New no-NULL native replay | per engine: 64 databases, 1,024 SQL executions and 1,024 SQL--CQ set comparisons, all agree | `results/native-study/summary.json` |
| Native lifecycle study | 120 trials; five runners; all snapshot results agree | `results/native-study/` |

The sixteen cascades are parameter cases of one construction, the eight graph controls are generated controls rather than public workloads, and the twenty-four ablations are not independent workload families. Finite counts validate implementations and exact instances; universal claims rely on proofs.

The current component checks also passed on Windows with Python 3.12.14 and SQLite 3.53.1: all 56 certificates and the checked frozen semantic outputs agreed, including the tiny oracle, graph partitions, mutations, and SQL replay. The added family tests check 67 admitted graphs on two through four vertices (8,923 image partitions) against the separate coloring oracle and 30 cascade key subsets through depth four against the run-length formula and legal witnesses. These are additional generated checks, not public workloads. The Windows checks did not execute `reproduce.py` or validate its Linux resource telemetry. The bounded Ubuntu workflow subsequently completed in run 37444167245: five stages, 48 tests, 246 matching scientific files and 56 certificate rechecks, with zero process swap. It recorded 4.576 wall seconds and 4.280 CPU seconds, 21,284 KiB largest-child RSS and 48,676 KiB parent RSS. SQLite 3.45.1 differs from the frozen 3.46.1 metadata; all semantic results agree, and DuckDB was not executed. Current run records are in `results/measurements/`.

For every cascade case, the syntax machine has eight reachable states, current output has two classes, and future behavior has four classes. With all identifier keys, depths one through six have minima 3, 7, 15, 31, 63, and 127. Without nonroot identifier keys, the minima are 3, 5, 7, 9, 11, and 13. At depth seven the all-key theorem gives 255; that over-cap database is not materialized.

## Public SQL and engine control

The original JOB `1a`–`1d`, `2a`–`2d` sample is retained separately under `inputs/job-negative/`: all eight use `MIN` and are excluded unchanged. The manifest records the pinned commit, immutable Git blob identifiers, minimal excerpts, and exclusion reasons. Because the JOB mirror declares no repository license, complete query files are not redistributed. This is neither a full-JOB census nor a transformed-query experiment.

Positive public evidence comes from SQLSolver's Calcite equivalence tests at commit `dcc2a91d8971a4c4d30b055f99d7d8428a1b754b`, redistributed under Apache-2.0 with its license and notice. `inputs/public/manifest.json` records source lines, exact SQL, schema, and the admission rule. The eight CQ adapters are hand-written, not parser output. `inputs/public/adapter-contracts.json` and `inputs/public/ADAPTER-CONTRACTS.md` specify column positions, projections, equalities, output types, and the finite SQL-null correspondence; tests require those records to match the executable cases. Each two-state pair has a one-state quotient certificate.

The retained host reports SQLite 3.46.1, but that version string is environment metadata rather than a claim-bearing equality field. SQLite evaluates all sixteen original statements on sixty-four deterministic legal databases: the 1,024 SQL executions agree within each pair for bags and sets. The same run performs 1,024 per-side set comparisons against the hand-written CQ adapters; all agree, while a corrupted projection is detected on 40 databases. Fifty SQL input cells contain `None`; each is mapped to a distinct fresh integer only for this finite adapter check. The theory itself has no nulls. The historical DuckDB record remains `NOT_RUN_PACKAGE_UNAVAILABLE`; the new execution below is separate.

## Native snapshot execution and complete costs

[NATIVE-STUDY.md](NATIVE-STUDY.md) specifies the optional DuckDB/SQLite study,
five runners, data, updates, complete cost boundary, and portable commands. It
reuses the original SQL, adapters, schema, producer, and verifier. Its separate
no-NULL replay passes 1,024 original-SQL executions and 1,024 adapter comparisons
per engine, detecting the corrupted projection on 40/64 databases in both.

The 120 file-backed trials use SQLite 3.53.1, DuckDB 1.5.6, Python 3.12.14,
Windows 11 build 28000, an Intel Core i7-12700KF (12 cores/20 logical
processors), and 34,190,049,280 bytes of physical RAM. Each engine uses one
worker. Two initial sizes (128/1,024 employees), two reuse levels (80/640 total
requests), five runners and three repetitions include four committed,
result-changing update transactions and final close/reopen verification.

The composed public-query workload has 16 reachable control states, 8 quotient
states and 4 current-output classes. A cache keyed by quotient state makes 40
workload SQL executions over five snapshots; output-equivalence caching makes
20, with either original or quotient routing. Both matched-information runners
are charged the same full certificate construction and checking. At 1,024
employees and 640 requests, median full totals are 171.153/163.913 ms for
SQLite original/quotient routing with output caching, and 245.164/247.929 ms for
DuckDB. These three-repetition observations do not establish a stable routing
speedup. At 128 employees and 80 requests, SQLite quotient-block caching costs
42.236 ms versus 40.519 ms direct execution, despite fewer native workload
executions. No database tuples are removed; final file sizes are unchanged
between runners within an engine and data size.

All original-statement validation, loading, certificate setup, updates,
checkpoint/close and reopen validation are inside the outer totals. The 112
validation SQL executions per trial are separate from workload execution
counts. Validation warms the engine before request timing. Raw trials, stage
medians/ranges, settings, the composed workload and its 28-separator certificate
are retained in `results/native-study/`; this study does not overwrite the
original resource measurements or change the five-stage reproduction census.
Eight additional native regressions are run directly as described in the study
document, outside that census.

## Proof schematics

The proof schematics have a separate optional drawing dependency:

```sh
python3 -m pip install -r requirements-figures.txt
python3 figures/draw_schematics.py
python3 figures/check_figures.py
```

The standalone renderer writes the two current vector PDFs in `figures/`,
checks label bounds, and requires neither TeX nor a sibling manuscript.
The figure check regenerates both into a temporary directory and compares their
bytes. These checks are separate from the frozen five-stage scientific census.

## Resource contract

The wrapper uses one worker, a 2.5 GiB address-space ceiling, 240 CPU seconds and 300 wall seconds per child, zero accepted process swap, no more than 500,000 conservative obligations and 100,000 tiny legal valuations, 256 raw chase records, and 128 materialized tuples per generated witness. The retained five-stage run charged 103,007 main obligations, 4.045533611 CPU seconds and 4.219736089 wall seconds, with 97,324 KiB largest-child RSS, 127,268 KiB parent RSS, and zero process swap. `results/clean-reproduction.json` lists every addend and the checks excluded from that heterogeneous counter. These values establish closure, not speedup.

## Organization

- `src/workload_identifiability/` — producer, independent verifier, generators, image search, explicit public-case adapters, engine replay, and CLI.
- `proofs/` — four standalone proof notes aligned with the manuscript.
- `inputs/` — all generated cases, mutations, tiny model, public SQL, manifest, and negative screen.
- `results/` — complete certificates, witnesses, partitions, oracle records, engine results, logs, and summaries.
- `tests/` — 54 main regression methods and two separately invoked suffix regressions.
- `claim_evidence_ledger.csv` — every material claim mapped to proof/check/result/table and maturity.
- `external_resources.csv` — source, URL, license/access note, acquisition, and integration inventory.
- `reference-verification.csv` — records for all 50 cited bibliography keys: 41 historical rows retained and nine added primary-source metadata/bounded-context checks, with each check's extent in its notes. The added rows do not certify complete-source reading.
- `literature-reading.csv` — the 22-paper calibration plus two additional close readings.
- `THIRD-PARTY-NOTICES.md` and `third_party/` — redistribution notices.

The repository does not require the paper directory, a private path, an omitted cache, a network service, a model API, or an external controller.

Producer joins retain stable atom order and lexicographic row order, but prepare a relation's ordered rows only on its first visit within one `matches` call. This local reuse does not alter the independent verifier or image enumeration. The six self-contained `test_match_rows.py` methods compare 12,288 complete ordered matches with a literal Cartesian reference and 2,048 answer sets with the verifier's separate evaluator; they also check duplicates, first-map choice, lazy/call-local reuse, unchanged counters and admission limits, and checker independence. Run them portably with `python3 -m unittest discover -s tests -p test_match_rows.py -v`. They passed as finite component checks, not a full 54-test Linux reproduction or a timing measurement.

Two supplementary methods in `tests/regression_suffix_bound.py` check the
distinguishing-suffix length bound over 4,330 finite unary machines and tight
chains of two through eight states. Run this script directly, in normal or
optimized interpreter mode. CI runs both modes before the unchanged 54-method
reproduction census. Paper-build tests remain in the manuscript package, so
the standalone artifact has no dependency on a sibling paper directory.

The general distinguishing-suffix bound follows from `proofs/quotient.md`.

## Interpretation and external-use boundary

The frozen artifact is a complete internal research package for the stated fragment, not evidence of acceptance. No independent human proof/code audit was performed. Before any external submission, accountable human authors must independently verify the work and recheck live venue rules.
