# Trusted input, proof objects, and execution limits

## Trusted model

A model is UTF-8 JSON with `schema`, `queries`, `alphabet`, `states`, and
`initial`. A relation declares a positive `arity`, one or more nonempty keys
(as zero-based column-position lists), and optional `fks`. Each foreign key has
`source`, `target`, and `columns`, with `columns` exactly one of the target
relation's declared keys. Positions are ordered consistently when comparing
foreign-key source and target tuples. The producer rejects a cycle in the
relation dependency graph even when all input queries are acyclic.

Each query has `atoms`, `head`, and optional `equalities`. An atom is
`[relation_name, term_list]`. A variable is `v:<name>`. A constant is `c:<integer>`
using the canonical decimal spelling: `c:0` and `c:-3` are allowed; `c:00`,
`c:+1`, and `c:-0` are rejected. Variables in guards and the ordered output must
occur in an atom; constants may also occur only in a guard or output. All queries
in a workload have the same output arity; an empty output is Boolean. Repeated
variables, self-joins, projections, and explicit equalities are supported. A
contradictory equality guard denotes a false query. Only integer equality is
interpreted: there is no ordering, arithmetic, implicit cast, null, or bag
multiplicity.

A state declares a query index and a `next` dictionary containing exactly one
successor for each action. Actions are finite concrete strings. The state at
`initial` is the only reachability root. Unreachable states are excluded from
the quotient. To inspect a complete small input, use
`inputs/cascade/families/case-01.json`. Relation and query names do not cause code
execution; the programs do not evaluate strings as Python or SQL.

## Quotient certificate

A certificate contains a chase for **every catalogue query**, every directed
containment entry, a reachable-state partition, and one actual separating
word/database for **every pair of distinct blocks**. Positive containment
entries are head-preserving maps, or justified source inconsistency. Negative
entries are not trusted search failures: the verifier grounds the independently
replayed source instance and checks that its distinguished answer is present
in the source and absent in the target. Fresh grounding avoids constants in
all atoms, guards, and heads, including constants found only in a target query.

Chase rows record a seed atom or the exact parent and foreign-key edge that
introduced them. The verifier requires all outgoing foreign-key expansions,
fresh non-key terms, and copied target-key terms. Every equality step cites an
input guard or two current key-agreeing rows and the enforced equality. An
inconsistent chase must finish with a justified collision of different rigid
constants. Otherwise all guards, keys, and foreign keys are checked on the
normalized finite facts.

The verifier uses flat equivalence-class rewriting rather than the producer's
union-find. It evaluates original atoms in original order with eager guards,
rather than importing the producer's relational matcher. A complete stable
partition prevents unsound merging. Actual separators for all distinct blocks
prevent unsound splitting. The quotient proof is mathematical; these two
implementations are implementation diversity, not independent researchers.

`trusted_input` checks the finite representation and key/FK/query shapes. The
producer additionally checks the promised acyclic fragment using relation-graph
traversal and GYO reduction. The verifier need not infer acyclicity to validate
an explicitly complete finite legal universal construction. Thus its
acceptance is a semantic statement about a supplied valid finite proof, not a
second claim that every accepted input was run through the same fragment
admission algorithm. General completeness of the producer is restricted by its
stated execution caps.

Fields recording refinement history, syntactic baseline counts, and charged
search work are diagnostic producer measurements, not trusted proof premises.
Acceptance does not certify a latency measurement, a minimum-size database, or
that a supplied separator is the shortest possible word. The producer's pair
search returns a shortest separating suffix; the certificate only needs a valid
one within the proved sufficient length bound. Witness-size optimality is
established separately by the cascade/graph proofs or an exhaustive legal-image
search covered by the image theorem.

## Exact legal-image search

Image search takes two query indices, a source chase, and all rigid constants
from the model. It enumerates each partition of the remaining source names into
existing constant classes or canonically numbered fresh classes exactly once.
For each partition it maps the source facts, deduplicates tuples under set
semantics, checks all keys and FKs, and rejects any image whose distinguished
source answer occurs in the target. It may identify a source name with a target-
only constant; those candidates cannot simply be omitted.

Every outcome is retained as a JSON line under `results/graphs/partitions/`.
The accompanying image file records the complete enumeration count and one
minimum, or that no directed counterexample exists. The proof that this finite
space contains a global optimum uses a legal image of the universal source
inside any given legal countermodel. It depends on **linear foreign keys** and
positive target queries. It is not asserted for joined-body dependencies or
negation. Exhaustion after a preflight/time limit is `UNKNOWN`, not optimality of
the best model seen so far.

## Bounds and failure meanings

The CLI applies one-CPU affinity when available, a 2.5-GiB address-space limit,
240 CPU seconds, and a 300-second alarm. It uses no network or child processes.
The full reproduction wrapper launches one such subprocess at a time and waits.
At most 256 unfolded records and 128 normalized tuples are admitted per query;
concrete witnesses are capped at 128 tuples. A symbolic-record count is not a
normalized tuple count: at cascade depth six a joined seed has 190 symbolic
records but 127 distinct normalized facts.

A single producer invocation preflights its charged semantic/search work at
500,000. The checker separately caps block-pair obligations at 500,000 before
allocating them. The fixed campaigns and full reproduction summary report their
aggregate counts; these are not counts of every Python operation or tuple
comparison. Image search preflights eight names and 10,000 partitions, and the
tiny-oracle campaign caps legal valuations at 100,000. The frozen campaign is far
below these limits; no result relies on raising a cap after seeing an outcome.

`REJECTED` reports an invalid trusted representation, a false proof obligation,
or an operational input/output failure; read its reason rather than interpreting
all such results as query inequivalence. `UNKNOWN` reports a resource/admission
bound and has no semantic implication. An OS-enforced hard CPU limit can also
terminate a process without a JSON response; absence of an accepted completion
record is never treated as success. Outputs are exclusively created. No failed
run overwrites or erases existing scientific evidence.
