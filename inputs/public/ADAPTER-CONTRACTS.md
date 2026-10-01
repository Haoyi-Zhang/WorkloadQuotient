# Hand-written SQL-to-CQ adapter contract

The eight executable adapters are hand-written; the artifact does not contain a general SQL parser or a verified SQL-to-CQ compiler. `adapter-contracts.json` records the exact two SQL statements, table/column order, projection, equality predicates, SQL output types, nullable columns, and the corresponding executable CQ for every pair. Unit tests require this contract, `manifest.json`, and the eight case files to agree exactly.

The finite comparison uses the published `DEPT(DEPTNO, NAME)` and `EMP(EMPNO, ENAME, JOB, MGR, HIREDATE, SAL, COMM, DEPTNO, SLACKER)` column order. SQL integers are preserved, so rigid CQ constants such as `1` and `10` retain their values. Text values are injectively encoded as integers disjoint from SQL integer values. Each input `NULL` cell is assigned a different fresh integer. No selected output may be `NULL`. This last device prevents SQL `NULL` cells from being treated as equal in the retained comparisons, but it is only a finite test encoding: the paper's theory remains a no-`NULL` integer domain and makes no general SQL `NULL` claim.

| pair | left projection / equalities | right projection / equalities | output |
|---|---|---|---|
| public-01 | `EMP.ENAME`; `EMP.DEPTNO=DEPT.DEPTNO` | `EMP0.ENAME`; same join under aliases | non-NULL text |
| public-02 | `EMP.MGR`; `EMP.MGR=10` | rigid `10`; `EMP0.MGR=10` | non-NULL integer after the filter |
| public-03 | first `EMP.ENAME`; two `DEPTNO` joins | same three atoms under aliases | non-NULL text |
| public-04 | first `EMP.ENAME`; department join and `EMPNO` self-join | same result with two additional key-redundant lookups | non-NULL text |
| public-05 | rigid `1`; `EMP.DEPTNO=DEPT.DEPTNO` | rigid `1`; same join under aliases | non-NULL integer |
| public-06 | derived-table `NAME`; duplicate `DEPTNO=10` after flattening | `DEPT0.NAME`; one `DEPTNO=10` guard | non-NULL text |
| public-07 | rigid `1`; two `EMP` atoms joined on `DEPTNO` | same under alpha-renaming | non-NULL integer |
| public-08 | rigid `1`; one `DEPT` lookup | rigid `1`; a second lookup on the same declared key | non-NULL integer |

For each of the 64 deterministic legal SQL databases, SQLite executes both unchanged SQL statements. The artifact separately evaluates each corresponding hand-written CQ on the explicit integer encoding and compares deduplicated result sets side by side. A deliberately corrupted adapter (projecting `JOB` instead of `ENAME` for public-01) must disagree on at least one database. Bag equality is reported only for the SQL pair itself; no CQ bag-semantics claim is made.
