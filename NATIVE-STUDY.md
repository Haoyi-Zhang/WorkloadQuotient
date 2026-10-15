# Native snapshot execution and lifecycle costs

This optional study reuses the eight pinned SQLSolver Calcite pairs, their
hand-written CQ adapters, schema, certificate producer, and separate verifier.
It requires the public `duckdb` Python package in addition to the standard
library. It does not change the original Linux reproduction or its frozen
counts. SQL provenance and Apache-2.0 notices remain in `inputs/public/` and
`third_party/sqlsolver/`.

The optional package is pinned in `requirements-native-study.txt`. DuckDB's
[official PyPI distribution](https://pypi.org/project/duckdb/1.5.6/) is
MIT-licensed; the package is an external dependency, not redistributed here.

## Workload and comparison

The sixteen unchanged SQL statements label a sixteen-state phase/copy machine.
`clone` toggles the copy in the current pair; `next` advances to the next of the
eight public pairs, preserving the copy bit. All states are reachable. This is
a constructed trace over existing public queries, not a production trace. Each
snapshot sweeps through all sixteen states either once or eight times.

Five runners serve exactly the same requests and ordered-tuple **sets**:

| Runner | Routing | Answer-cache key | Certificate cost |
|---|---|---|---|
| `direct` | Original machine | None | None |
| `literal_cache` | Original machine | Original SQL index | None |
| `quotient_cache` | Certified future-behavior quotient | Quotient state | Produce and verify |
| `output_cache` | Original machine | Certified current-query equivalence | The same complete certificate, produced and verified |
| `quotient_output_cache` | Certified future-behavior quotient | Certified current-query equivalence | The same complete certificate, produced and verified |

The last two runners form the matched-information control: semantic equivalence can
support answer reuse without replacing the routing machine by its quotient.
Current-output classes need not be a transition congruence; they are never used
as routing states. Representatives are the first query index in a class, not a
query selected after timing. The quotient minimizes control states; it does not
minimize this cache's keys or native execution cost.

Both engines load identical no-NULL data. The initial sizes are 128 and 1,024
employees, with 16 and 128 departments. The generator preserves keys and the
employee-to-department FK, repeats nonkey names, and keeps approximately eight
employees per department. It generates data rather than copying a production
database. The workload does not compress database tuples.

Four committed transactions separate five read-only snapshots:

1. Insert a new employee in department 10.
2. Rename department 10 and employee 1.
3. Reassign employee 2 to department 10 and set every manager to 11, making the
   selected `MGR=10` result empty.
4. Delete the inserted employee.

Every transaction changes at least one selected set result. All answer caches
are discarded at the snapshot boundary. The schema/query certificate remains
valid because the updates preserve the fixed schema, keys, and FK. These
transactions are not actions in the read-only workload theorem. No incremental
view-maintenance algorithm is claimed.

## Cost boundary

Each independently initialized, file-backed trial includes input/adapter
contract reading, data generation, certificate construction and separate
checking where applicable, routing-table construction, database open and DDL,
transactional loading, all request executions, complete row fetching and set
normalization, answer checking, cache destruction, committed updates, data and
dependency validation, checkpoint/close, and reopen/final result verification.
The outer wall interval includes unallocated bookkeeping. `produce_s` and
`verify_s` are **subcomponents** of `plan_s`, not additional summands. CPU time
is also recorded. Stage medians need not sum to the median of the outer total.

All sixteen original statements are rerun for validation at every snapshot,
again at the final snapshot, and after reopening. Their sets and the stored
tables must agree across engines, runners, sweeps, and repetitions. These
validation queries warm the engines before request timing; `query_s` is not a
cold-plan or cold-cache latency result. `total_s` includes that validation work.
The engines' normal statement/plan caches are not disabled. Bag rows are
fetched before deduplication, including the public self-join multiplicities.

SQLite enables FKs, `synchronous=FULL`, DELETE journaling and one worker.
DuckDB uses one worker, declared PK/FK constraints and its default storage
settings. These engine settings are not a claim of identical crash-durability
semantics. All methods within an engine use identical storage settings and
fresh files. Engine-specific loading, indexing, commit and checkpoint costs
remain in the totals. Final database-file size is recorded; it is not process
memory, cache memory, or a tuple-compression measurement. Native modules are
imported before the trials; package installation and study-wide finite replay
are outside each trial's lifecycle. Three repetitions rotate method order and
alternate engine order. No significance test is inferred from three runs.

## Native result track

The existing 64-database generator is also replayed in both engines, replacing
its nullable manager cells with the ordinary value 11 **before** execution.
The SQL text and CQ adapters are unchanged. This new no-NULL track has 1,024
SQL executions and 1,024 SQL-set/CQ-set comparisons per engine, with the
existing corrupted-projection control. It is separate from the historical
SQLite replay that contained nullable input cells. It does not replace that
record or establish SQL NULL semantics.

## Commands and outputs

Run from the artifact root with its `src` directory on `PYTHONPATH`. Install
DuckDB in a private virtual environment or target directory, never by changing
the system Python for this experiment. The recorded package is DuckDB 1.5.6.

```sh
python -B -m workload_identifiability.native_study \
  --output /absolute/new-native-results \
  --work /absolute/new-private-database-directory
python -B tests/regression_native_study.py --work /absolute/private-scratch -v
python -B -O tests/regression_native_study.py --work /absolute/private-scratch -v
```

The output/work directories must be fresh; no existing results are overwritten.
The retained scientific outputs are `results/native-study/workload.json`,
`certificate.json`, `trials.jsonl`, and `summary.json`. The summary contains
environment versions, all 40 condition medians and ranges, both native replay
records, and the full accounting boundary. `trials.jsonl` retains every stage,
request/execution count, tuple count and file size for all 120 trials. Temporary
database files and command logs belong in the caller's private work directory,
not in the source distribution. The regression script is separate from the
54-method original reproduction census and names which native engines ran.
