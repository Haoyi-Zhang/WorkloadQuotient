# Third-party material and research provenance

The executable repository uses only the Python standard library. It does not
vendor a database engine, solver, learned model, benchmark dataset, or third-party
implementation. Its generated models and databases are retained in full. Source
URLs and the licenses that were actually established are listed in
`external_resources.csv`.

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

Substantive AI assistance was used in formulation, proof development, literature
analysis, implementation, test construction, execution analysis, and manuscript
preparation. Producer and checker are separately implemented but were developed
within the same research process. They are not separate human reviewers, a blind
external review, or a proof-assistant kernel. No external model API or model
execution was used by the experiments. No external submission or public upload
is represented as completed.
