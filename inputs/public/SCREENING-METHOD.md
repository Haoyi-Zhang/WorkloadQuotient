# Public SQL screening and provenance

## Frozen source

The positive public cases come from the Apache-2.0 `calcite_tests` file in the public SQLSolver repository at commit `dcc2a91d8971a4c4d30b055f99d7d8428a1b754b`. The source path is `sqlsolver_data/calcite/calcite_tests`; the accompanying key/foreign-key schema is `sqlsolver_data/schemas/calcite_test.base.schema.sql` at the same commit. The repository license and attribution are retained under `third_party/sqlsolver/` and summarized in `THIRD-PARTY-NOTICES.md`.

The source file stores one SQL statement per physical line and pairs consecutive lines. Source-line numbers in this artifact are zero-based. `public-screening.csv` records all 181 consecutive pairs encountered from lines 0–361. The preregistered rule was to scan in ascending source order and admit the first eight pairs whose two statements normalize, without changing their SQL semantics, to the locked equality-only set-SPJ fragment over the published `EMP`/`DEPT` schema. Alias renaming, duplicate equality guards, and flattening a projection/selection-only derived table are permitted. Both normalized queries must be alpha-acyclic.

## Retained positive evidence

`manifest.json` freezes the source repository, commit, path, rule, selected zero-based lines, admission reason, and exact SQL strings. `sqlsolver-selected.sql` preserves all 16 admitted statements unchanged except for adding terminating semicolons and provenance comments. Every `cases/public-XX.json` file retains the same SQL strings and line numbers next to the explicit finite-CQ adapter used by the theorem checker. The unit test `test_public_manifest_has_eight_unchanged_pairs` cross-checks these four representations and the eight `ADMIT` rows in `public-screening.csv`.

The executable artifact does **not** use a general SQL parser to derive the finite-CQ adapters. The adapters are explicit, reviewable translations of the retained statements. SQLite executes the unchanged SQL text on the deterministic legal-database suite; the theorem checker evaluates the explicit adapters. Agreement between those two paths is a finite cross-check, not a proof that an arbitrary SQL parser or optimizer preserves the fragment semantics.

## Exclusions and audit boundary

The exclusion rows deliberately use a conservative aggregate reason: a pair either lies outside the locked fragment or occurs after the eighth admitted pair. They are not represented as 173 individually adjudicated semantic diagnoses. The full upstream source file is identified by an immutable commit and path but is not redistributed wholesale; therefore an entirely offline reviewer can audit the admitted inputs and all downstream evidence, while re-running the complete sequential source scan requires reacquiring that pinned Apache-2.0 file. This limitation is recorded rather than presenting the retained selection table as an independently reconstructed parser trace.

The earlier Join Order Benchmark sample is a separate negative screen: JOB queries `1a`–`1d` and `2a`–`2d` contain `MIN`, so none is counted among the eight positive public cases. No aggregate was deleted and no rewritten JOB query was substituted.
