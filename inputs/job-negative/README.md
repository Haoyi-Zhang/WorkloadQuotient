# Independent JOB negative screen

This directory records the separate negative admission screen for Join Order Benchmark queries `1a`–`1d` and `2a`–`2d`. It is not the 181-pair SQLSolver screening table under `inputs/public-screening.csv`.

The immutable source is `gregrahn/join-order-benchmark` at commit `a39603662e023e449cb2121997a5034df9e02ebf`. Each manifest row stores the upstream path, Git blob SHA, immutable file URL, and the shortest excerpt needed to show the exclusion: every query projects at least one `MIN(...)` aggregate. Aggregation is outside the paper's locked positive equality-CQ fragment, so the admission result is 0/8. No aggregate is deleted and no rewritten JOB query is substituted.

The GitHub repository does not declare a repository license in its metadata and has no root `LICENSE` file at the pinned commit. For that reason this artifact does not redistribute the complete eight query files; it retains only minimal excerpts and immutable identifiers. Rechecking the complete original SQL requires retrieving those eight pinned upstream files. The negative-screen conclusion is therefore traceable but not a claim that the complete upstream files are locally mirrored.
