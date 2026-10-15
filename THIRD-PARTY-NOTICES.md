# Third-party material and research provenance

The core implementation and original reproduction use only the Python standard
library. The optional native snapshot study additionally requires the pinned,
MIT-licensed DuckDB package in `requirements-native-study.txt`; no database engine
or third-party implementation is vendored. The selected SQLSolver queries and
schema are redistributed under Apache-2.0 with their license and notice in
`third_party/sqlsolver/`. Generated models and databases are retained in full.
Source URLs and established licenses are listed in `external_resources.csv`.

The independent JOB negative screen under `inputs/job-negative/` retains only
the minimal `SELECT MIN(...)` excerpts needed to explain exclusion, the pinned
commit, filenames, immutable file URLs, and upstream Git blob identifiers. Redistribution rights for the complete SQL corpus were not
established; complete queries and IMDb data are not redistributed or used in the
experiments. Screening of these eight originals is not an offline-reproduced SQL
benchmark, a census of all JOB queries, or a test of transformed SPJ queries.

Scholarly papers are cited, not republished. No assumption that a public URL
implies an open redistribution license is made. The standalone repository does
not include the ACM class or bibliography style. Those unchanged assets and their
supplied LaTeX Project Public License remain in the separate paper directory of
the complete project.

Producer and checker are separately implemented but were developed within the same research process. They are not independent reviewers, a blind external review or a proof-assistant kernel. No external model API or model execution was used by the experiments.
