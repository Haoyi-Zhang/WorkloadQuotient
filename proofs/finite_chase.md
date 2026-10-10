# Finite universal instances for the declared fragment

## Objects and conventions

A schema has finitely many relation symbols of fixed finite arity. Each relation has at least one declared key, possibly several. A key K of R says that two R-tuples agreeing on every position in K agree everywhere. A foreign key R[I] -> S[K] has distinct source positions I, a declared target key K, and equally long ordered position lists. Every R-tuple must have an S-tuple agreeing on those lists. The directed graph with one edge R -> S for every FK is acyclic; parallel edges are allowed. All databases have set semantics over integers. Distinct written integers denote distinct values. There are no null values, inequality predicates, disjunctions, updates, or implicit arithmetic operations.

A query p is a safe conjunctive query with relational atoms, equality guards, and an ordered output tuple. Output variables and guard variables occur in relational atoms. Repeated variables, self-joins, repeated output coordinates, constants in the output, and the empty output tuple are allowed. A Boolean query returns either the empty set or the singleton containing the empty tuple. Explicit guards may be normalized first; the admitted query hypergraph is alpha-acyclic after this normalization. The proof below does not need query acyclicity. Dependency acyclicity, rather than query acyclicity, is what supplies the finite construction.

A symbolic instance consists of relational facts over rigid integer constants and finitely many freely assignable names. These names are not SQL NULLs. A homomorphism fixes all written constants and sends facts to facts; for a pointed instance it also sends the ordered distinguished tuple to the specified output tuple. Equalities in a query are requirements on its assignment.

## Construction

For each relation R, define B(R) recursively in reverse dependency order by

    B(R) = 1 + sum over FK edges e leaving R of B(target(e)).

Start with one raw record for each atom of p. Keep common query variables as common names. For every raw record and every FK leaving its relation, append a new target record. Copy the source FK positions to the target key positions and use globally fresh names in all other target positions. Do this for every appended record too. Each raw record has its unique seed or parent-edge origin. This is full FK-path unfolding; it intentionally does not suppress an expansion merely because another target might already exist.

Then identify names required by every explicit equality guard. Repeatedly enforce keys: if two records of the same relation agree modulo current identifications on a declared key, identify every corresponding position. Each nontrivial identification reduces the number of equivalence classes. If two distinct rigid constants must be identified, report inconsistency. Otherwise replace terms by their final equivalence-class representatives and delete duplicate facts. Call the resulting pointed instance C_p, with distinguished tuple h_p.

## Lemma F1: finite unfolding and finite equality saturation

If the query has atoms with relations R_1,...,R_m, full unfolding creates exactly U_p = sum_i B(R_i) raw records. Equality saturation terminates after at most max(0,T-1) successful nontrivial identifications, where T is the number of initially distinct terms, unless an earlier rigid-constant clash occurs.

**Proof.** Any descent from a seed follows a directed FK path, and a directed path in an acyclic relation graph has finite length. A record of relation R contributes itself and an independently created expansion subtree for each outgoing edge. Induction in reverse topological order therefore gives exactly B(R) descendants including that record. Distinct seeds and distinct parent-edge occurrences create distinct raw records, so summing gives U_p. There are finitely many terms. Each nontrivial identification merges two equivalence classes, and no step splits a class or creates a term. For T>=1, at most T-1 successful merges occur; for T=0, no pair exists to merge. An empty Boolean body without guards gives the empty legal instance and answer (), with zero merges. This mathematical boundary is outside the executable's separate nonempty-body admission. A finite rescan of the finite pairs and finite keys detects each new consequence until no merge remains. A clash is terminal. This proves termination, not a polynomial bound: the number of paths can be exponential in the dependency depth. QED.

## Lemma F2: extension of every legal satisfying assignment

Let D be any legal database, finite or infinite, and let a satisfy p's body and guards in D. Then a extends to an assignment of every raw unfolded record into D and is constant on every equivalence class produced by equality saturation.

**Proof.** Map each seed record by a. Process raw records in origin order. When an already mapped source record has an FK expansion, legality of D supplies at least one target tuple with the required key values. Map the newly introduced non-key names to the remaining coordinates of that target tuple. Freshness ensures that these choices do not conflict with any earlier choice; copied positions already have the correct values. The FK target is a key, so its witness is in fact unique for its key values, but uniqueness is not needed for the existence step.

Every explicit guard identification is respected because a satisfies the guard. Induct on the key-identification sequence. Its premise states that two mapped tuples agree on all key positions; previous identifications are respected by the inductive hypothesis. Since D satisfies that key, the tuples agree in every position, including the newly identified coordinate. The extension therefore respects every merge. Distinct rigid constants have distinct interpretations, so such an extension cannot respect a constant clash. QED.

## Lemma F3: legality and universality of a successful result

If no clash occurs, C_p is a finite legal symbolic instance under every injective grounding of its remaining names that avoids the written constants. Its distinguished tuple is an answer to p on C_p. For every legal D and every a in p(D), there is a homomorphism f:C_p -> D with f(h_p)=a. If a clash occurs, p has no answer on any legal database.

**Proof.** All equality guards hold after saturation. Seed facts establish the body of p and give its distinguished answer. Saturation says that two normalized facts agreeing on a key agree at all coordinates, so every key holds. For an FK and any normalized source fact, choose one raw source record giving that fact. That record has an appended target witness. After the same identifications, the normalized target still agrees on the FK positions; duplicate deletion does not remove its existence. Hence every FK holds. An injective grounding introduces no new equalities between distinct symbolic classes and preserves these properties.

For universality, apply Lemma F2 to an assignment witnessing a. Because the extension respects every identification, it factors through the equivalence classes and induces a homomorphism from C_p to D; the distinguished output becomes a. A constant clash contradicts Lemma F2 for any proposed satisfying assignment, proving unsatisfiability. Conversely, successful C_p has a legal finite grounding satisfying p, so success and satisfiability coincide. QED.

## Theorem F4: exact finite and unrestricted containment

For safe conjunctive queries p and q of the same output arity, p is contained in q on all legal databases if and only if either the construction for p clashes, or there is a constant-fixing, head-preserving homomorphism from q into C_p. The same criterion characterizes containment over only finite legal databases.

**Proof.** A clashing p is empty on every legal database. Otherwise suppose q maps to C_p and let a be any answer to p on a legal D. Universality supplies f:C_p -> D sending h_p to a. Compose the q-map with f. Relational facts, explicit guards, constants, and the ordered head are preserved, so a belongs to q(D). This establishes containment even for infinite D.

Conversely, C_p can be grounded injectively into integers avoiding *every constant appearing in either query*, including constants that occur only in a guard or the head of q. Its distinguished grounded tuple belongs to p. If finite containment holds, that tuple belongs to q, and a witnessing assignment to q can be pulled back through the injective grounding to a homomorphism into C_p. A target constant absent from C_p cannot be supplied accidentally by a fresh grounded name because those names avoid all target constants. Thus absence of a head-preserving homomorphism gives a finite legal counterexample. The two containment domains therefore coincide. QED.

## What this proof does not imply

Query acyclicity does not imply FK-chase termination. A schema R(x,y) with a key on x and FK R[y] -> R[x] already admits indefinite fresh unfolding from a one-atom query. This observation is about a construction, not proof that every cyclic-FK instance needs an infinite database or that equivalence under all cyclic FK classes is undecidable.

The path bound U_p is not generally 128. The executable producer additionally caps raw records at 256 and normalized facts at 128, and refuses inputs before publishing a certificate when those limits fail. This bounded implementation is sound on accepted instances, not a complete implementation for every finite DAG schema. The complete mathematical decision procedure is the unbounded finite construction plus finite homomorphism search. No empirical agreement is used to prove this theorem. The result specializes established chase/containment principles; it is not claimed as a new general containment theorem.
