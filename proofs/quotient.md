# Observation, the canonical quotient, and its certificate

## Finite concrete workloads

A workload W=(S,A,delta,s0,lambda) has a finite state set S, an explicitly finite action alphabet A, a total deterministic transition function delta:S x A -> S, an initial state s0, and an output query lambda(s) at every state. All output queries have the same output arity and the same schema. Extend delta to words in the usual way, including the empty word epsilon. Only states reachable from s0 are part of the minimization problem.

For a fixed legal database D and a word w, the terminal observation from s is lambda(delta(s,w))(D). Define

    s ~ t  iff  for every finite word w and every legal D,
                 lambda(delta(s,w))(D) = lambda(delta(t,w))(D).

The *same* D is used on both sides. Equality means equality of sets of ordered tuples, not equality up to renaming data values. Since every prefix is itself a word, this definition also preserves the entire sequence of output observations along a run. No database update occurs while a word is read.

An action is a concrete input label in this model. There is no inferred abstraction of an infinite stream of parameter values. Equality guards belong to output queries. Treating two stored distinct constants as interchangeable would change the observation relation: queries selecting R(a) and R(b) are distinguished on the fixed database {R(a)} when a differs from b, even though the isolated constants have the same one-element equality pattern.

## Theorem Q1: coarsest output-compatible right congruence

The relation ~ is an equivalence relation, preserves present output equivalence, is a right congruence for every action, and contains every output-compatible right congruence on the reachable states.

**Proof.** Reflexivity, symmetry and transitivity hold pointwise for equality of all observations. Taking w=epsilon proves present-output compatibility. If s~t and a is an action, then for every w,D the observations from delta(s,a) and delta(t,a) after w equal the observations from s,t after aw; those are equal by definition. Thus successors are equivalent.

Now let R be any equivalence relation that preserves present query outputs on every legal D and whose classes are stable under every action. Induction on word length shows that s R t implies delta(s,w) R delta(t,w) for every w. Output compatibility at those terminal states gives equal observations. Hence R is included in ~, proving coarseness. QED.

## Theorem Q2: terminating refinement computes ~

First partition reachable states by exact present-query equivalence, decided with Theorem F4 in both directions. Given partition P_i, form P_(i+1) by grouping states with the same present-query equivalence label and the same vector of P_i-successor blocks, in a fixed action order. Stop when the partition does not change. The fixed point is exactly ~.

**Proof.** The initial partition relates states with equal observations at epsilon. Inductively, P_i relates exactly states with equal observations for every word of length at most i. Indeed, agreement at epsilon is tested by the output label, and every nonempty word of length at most i+1 has a first action and a suffix of length at most i. Thus the sequence only refines. A strict refinement increases the number of blocks, so at most |S_reach|-1 strict refinements are possible.

At the fixed point the relation is output-compatible and a right congruence, and Theorem Q1 puts it inside ~. Conversely, states related by ~ have equal observations for all bounded lengths and are never separated at any refinement. Hence ~ is inside the fixed point. QED.

## Theorem Q3: state-minimality and uniqueness

The reachable quotient W/~ is well-defined, behavior-preserving, has the fewest reachable states among all deterministic workloads with the same initial behavior, and is unique up to initial-state-, transition-, and output-behavior-preserving isomorphism.

**Proof.** Right congruence makes the successor of a class independent of the chosen representative. Present-output compatibility makes its output function well-defined; one may choose any member query as its representation. Induction on words gives the same observations from the quotient initial class as from W.

For the lower bound, choose, for each quotient class C, an action word u_C reaching a representative of C. Consider any deterministic machine M with the same initial observations on all words and legal databases. If M reaches the same state after u_C and u_E for two different classes, it must have identical future observations after every suffix w from these prefixes. But C and E are inequivalent, so some w and D distinguish them. Equivalence of initial behaviors would make M both equal and unequal on that observation, a contradiction. Thus M must reach at least one different state per class. The quotient attains this lower bound.

For uniqueness, a reachable minimum machine cannot have two states with the same residual observation function, because merging their equal residuals produces a smaller behaviorally equivalent machine. Its states are therefore in bijection with residual observation functions of initial prefixes, and these are exactly the classes of W/~. Reading an action advances a residual in the same way in either machine. The empty prefix identifies the initial state, and the empty suffix identifies the output function. This residual-function bijection is the required isomorphism. It concerns semantic outputs, not identical SQL strings or arbitrary state numbering. QED.

## Lemma Q4: bounded distinguishing suffixes

For n reachable states, any inequivalent pair has a distinguishing word of length at most binomial(n,2)-1. The case n=1 has no inequivalent pair.

**Proof.** Run breadth-first search on unordered state pairs, starting with the pair. A pair whose present outputs differ is accepting. If no accepting pair is reachable, closure under actions gives identical observations for every word, contradicting inequivalence. A shortest accepting path contains no repeated unordered pair: deleting the segment between repeats leaves a shorter accepting path. No diagonal pair can lie on this path because deterministic successors of equal states remain equal and can never be accepting. There are binomial(n,2) non-diagonal unordered pairs, so the path has at most that many vertices and one fewer edges. Symmetry of output inequality makes forgetting orientation harmless. QED.

At the terminal pair, Theorem F4 supplies a finite legal database in one of the two failed containment directions. One such database is enough: no sequence of different databases is needed along the word. Shortest-word search does not by itself optimize database size, and we make no joint word-length/database-size optimization claim.

## Certificate and checking obligations

A certificate contains a justified finite chase for each output query; a complete directed containment matrix; a partition of exactly the reachable states; and a word with a concrete legal distinguishing database for every unordered pair of distinct proposed blocks. Chase records carry seed or FK origins. Equality merges carry an explicit guard or a key-premise reason. A successful chase is checked for final key/FK satisfaction. A failed chase must end in a justified clash of two distinct rigid constants.

Every positive containment entry is a checked, head-preserving query homomorphism or a justified empty-source case. Every negative entry is checked by independently evaluating the source and target on an injectively grounded source chase and its distinguished answer; a producer's failure to find a homomorphism is not trusted as a proof.

The checker independently computes reachability, checks present-output equality within blocks in both containment directions, and verifies successor-block equality for every member/action. These obligations prove that the proposed partition is contained in ~. It then verifies a genuine legal distinguishing database and trace for every pair of distinct blocks. If a true equivalence class had been split across proposed blocks, no such witness could exist. These pair witnesses therefore prove that ~ is contained in the proposed partition. Acceptance establishes exact equality with the minimal quotient, subject to correctness of the checker implementation and the stated input semantics.

The producer and checker use separate relational evaluators and separate equality-class implementations. This is implementation diversity, not an external review and not a proof assistant's verification of the general metatheorems. Malformed certificates are rejected; operational limit exhaustion returns UNKNOWN. Certificate size can be quadratic in the number of blocks because every block pair is represented. No subquadratic certificate or optimal checking-time claim is made.

## Running workload used in the finite tests

Take two inequivalent outputs p_plus and p_minus, each with a syntactically different but semantically equivalent FK-joined copy. Form phases 0,1,2,3, each with copy bit 0 or 1. The action next increments the phase modulo four and preserves the bit; clone toggles the bit and preserves the phase. Phases 0 and 1 output p_plus, phases 2 and 3 output p_minus; the bit chooses the syntactic copy. Both actions are total and all eight states are reachable.

The two copy states of a phase are equivalent. Different phases are distinguished either now (opposite signs) or after next (the two same-sign adjacent phases). Hence there are exactly four quotient states, two current-output classes, and eight states under literal-query-label refinement. Every pair needs a word of length zero or one. This construction demonstrates congruence and the need for future observations; its regularity is not evidence about the diversity of practical query workloads.
