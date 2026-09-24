# Minimum legal images, depth-one hardness, and nonunique optima

## Directed countermodel size

For two queries p,q of the same output arity, define mu(p,q) as the minimum total tuple count of a finite legal D having some a in p(D) minus q(D). Define mu(p,q)=infinity when this directed difference is impossible. Symmetric separation has optimum min(mu(p,q),mu(q,p)). The source answer is existentially chosen; it is not a prescribed complete result relation.

Let C_p be a successful finite universal instance from Lemma F3, with distinguished tuple h_p. A legal image is an instance f(C_p) produced by a map fixing all written constants, such that the image satisfies every key and FK. The map need not be injective and need not be an endomorphism of C_p. Require additionally that f(h_p) is not an answer to q on that image.

## Theorem I1: complete finite image characterization

If C_p exists, then mu(p,q) is exactly the minimum tuple count of a legal image f(C_p) satisfying the negative condition. If p is inconsistent, mu(p,q)=infinity.

**Proof.** Every such image contains the mapped seed facts and respects the source guards, so f(h_p) is an answer to p. The required negative condition excludes it from q. Every admissible image is therefore a directed countermodel, establishing one inequality.

For the other, take any finite legal D and a in p(D) minus q(D). Lemma F3 gives a homomorphism f:C_p -> D with f(h_p)=a. Let I=f(C_p); by definition its facts are a subset of D's facts. Keys are hereditary under taking a subset of facts: a violating pair in I would be a violating pair in D.

FK preservation needs a separate argument because arbitrary subinstances of a legal database need not satisfy FKs. Take an I-fact and one of its FKs. Choose a C_p-fact mapping to it. That source fact has a target witness inside C_p because C_p is FK-closed. The image of this target witness is a fact of I satisfying the required FK. Hence I is FK-closed. This argument uses the one-body-fact nature of an FK; it does not establish image closure for arbitrary dependencies with joins in their premises.

Since q is positive, q(I) is included in q(D). Thus a remains absent from q(I). The mapped source facts show a belongs to p(I), and |I|<=|D|. A minimum countermodel exists whenever any finite countermodel exists, because the possible finite sizes form a nonempty set of nonnegative integers. Applying the construction to a minimum one yields a legal separating image of no larger size. Combining both inequalities gives equality of minima. An inconsistent source has no directed countermodel by Lemma F3. QED.

The theorem uses a positive target even though the separating property itself is a difference of query answers. With a nonmonotone target, removing facts can create target answers and the subset step fails. The image legality check is also essential: an arbitrary quotient can create key collisions, even though FKs themselves are preserved under images of FK-closed instances.

## Corollary I2: an exact finite search without a tuple-bound assumption

Collect all rigid constants occurring in either query, including constants only in heads or guards. Add these as distinguished anchors even if some do not occur in C_p facts. Enumerate all partitions of C_p's nonconstant names together with these anchors, never identifying two different anchors. A nonconstant name may join an anchor class or another name's class. Give every remaining class a different fresh integer not equal to an anchor. Form the image database, reject key violations and failing negative conditions, and choose the fewest tuples.

Every map from the finite name set to integers induces one such equality pattern. Conversely, every pattern is realizable because the integer domain is infinite. Query answers and constraints use only equality, so replacing fresh integer representatives by other fresh representatives cannot change the result. Theorem I1 therefore makes the exhaustive partition search exact over *all* finite legal databases, not just databases whose constants were guessed in a bounded interval. The finite proof supplies the search space; observing finitely many examples does not supply the proof.

With b anchor classes and n remaining names, a restricted-growth enumeration satisfies F(0,b)=1 and F(n,b)=b*F(n-1,b)+F(n-1,b+1). The first name either joins one of b existing classes or starts the one new class; the same argument recurses. This counts all constant-respecting partitions without assigning arbitrary labels to indistinguishable fresh classes. Growth can be superpolynomial. The executable search preflights at most 10,000 partitions and eight nonconstant names; exhaustion or a timeout returns UNKNOWN, never an optimality claim for a best-so-far witness.

## A height-one encoding of graph coloring

Let G=(V,E) be a simple graph with n>=2 vertices numbered 0,...,n-1 and m edges. Construct a relation C(color) with its one column as key. For each i from 0 to n-2 create a distinct relation T_i(left,right), with the pair as key and one unary FK from each coordinate to C. For each edge e=(u,v), create a distinct relation E_e(side,color,marker), with two keys (side,color) and (color,marker), and a unary FK from color to C. Every FK targets C, so the dependency graph has height one. Maximum relation arity is three; the two keys of E_e are incomparable.

The positive Boolean query P_G has the following atoms:

    T_i(x_i,x_(i+1)) for each 0<=i<n-1;
    E_e(0,x_u,0) and E_e(1,x_v,0) for each e=(u,v).

Let Q_false be the Boolean query C(z) with the equality guard 0=1. No inequality predicate appears in P_G or Q_false. Let beta=n-1+2m, the number of positive-query atoms outside C.

## Lemma H1: acyclicity, satisfiability, and a rigid core

P_G has a connected alpha-acyclic hypergraph, is satisfiable under the schema, and its source chase is a rigid core with beta+n facts.

**Proof.** The bridge atoms T_i have hyperedges {x_i,x_(i+1)}, forming a path. Each E atom contributes only a singleton hyperedge because its other positions are constants. Attach it to a bridge bag containing its variable. Each variable's bags are connected, giving a join tree. The bridge path includes every vertex, including isolated graph vertices, so the query hypergraph is connected. Self-joins are present because E_e occurs twice; their two occurrences are separate query atoms.

Assign a different fresh integer to every x_i. Populate each T_i with its one required tuple, each E_e with its two required tuples, and C with all n integers. Every key and FK holds. Thus the query is satisfiable.

The source canonical instance has these same facts with distinct symbolic names for the vertex colors. Full unfolding creates repeated unary C witnesses, which deduplicate to n facts. No key identifies different vertex names, because different fresh names do not agree on an edge's (color,marker) key. An endomorphism must fix the unique tuple in each separately named T_i relation, so it fixes both coordinates of that tuple. Together these tuples fix every vertex name. Constants are fixed by definition, so all facts and terms are fixed. The instance is rigid and hence a core. QED.

## Theorem H2: exact chromatic optimum

The minimum total size of a finite legal database distinguishing P_G from Q_false is

    beta + chi(G).

If the secondary key (color,marker) is kept only for edge set H subset of E, replace chi(G) by chi((V,H)); beta still counts all original edge atoms.

**Lower bound.** Any distinguishing database satisfies P_G because Q_false is always false. A satisfying assignment uses a tuple in each distinct T_i relation, giving at least n-1 tuples. For every edge relation, the two query atoms require different side values 0 and 1, so they require two different tuples, giving at least 2m. When the (color,marker) key is present, assigning x_u=x_v would make these two tuples agree on that key but disagree on side, contradicting legality. Thus the assigned colors form a proper coloring of the retained-edge graph. At least chi colors occur. All vertex variables occur in the bridge path and its unary FKs force every assigned color into C. Therefore C contains at least chi facts. Summing yields beta+chi.

**Upper bound.** Choose a coloring with exactly chi colors and represent them by distinct fresh integers. Put the one required tuple in each T_i and the two required tuples in each E_e, and put exactly the used colors in C. Bridge pair-keys hold because each bridge has one tuple. The (side,color) key holds because each edge has just one tuple of each side. For a retained secondary key, proper coloring gives different colors and hence different key values; for an unretained edge this key is not required. Every unary FK holds. The database satisfies P_G and has exactly beta+chi facts. QED.

## Theorem H3: NP-completeness in combined input size

Consider the decision problem whose input is a schema of arity at most three with a height-at-most-one FK dependency graph, two alpha-acyclic Boolean conjunctive queries with equality guards, and a nonnegative binary integer B. Decide whether some finite legal database of at most B tuples distinguishes the queries. This problem is NP-complete. The result is about unbounded combined schema/query input, not the fixed 12-relation/12-atom execution envelope.

**NP-hardness.** Given an instance G of graph 3-colorability with n>=2, construct the schema and query pair above and set B=beta+3. The construction is polynomial in n+m, all stated structural restrictions hold, and Theorem H2 gives a distinguishing database of size at most B exactly when chi(G)<=3. Graph 3-colorability is NP-complete, supplying the reduction. Here finding *some* difference is trivial because assigning n distinct colors always works; the hardness is in minimizing the legal database, not in detecting that Q_false differs from a satisfiable query.

**Membership.** In a height-one dependency graph, every non-sink relation points only to sinks. Unfolding a query with k atoms therefore creates at most k*(1+f) raw facts, where f is the maximum number of outgoing FKs on any source relation. This quantity is polynomial in the total input size. Equality saturation cannot add facts. By Theorem F4, any inequivalent pair has a finite legal countermodel of this polynomial size. If the answer is yes for a smaller B, take such an at-most-B witness; if B is at least the polynomial bound, a polynomial-size witness suffices. In either case, there is a yes-certificate with polynomially many tuples. Because only equality is used, unnamed values can be renamed to distinct short fresh integer representatives preserving all written constants, making its encoding polynomial in input size.

Keys and FKs can be checked by finite comparisons or indexed projections in polynomial time. Boolean alpha-acyclic query evaluation is polynomial in combined query and database size: normalize equality guards and constants, obtain a join tree, replace each atom by its matching input tuples, perform semijoins from leaves to a root and back if all surviving tuples are needed, and test for a nonempty root. The running-intersection property ensures that any surviving root tuple can extend independently through all subtrees; conversely every satisfying assignment survives the semijoins. With maximum arity three, the per-bag tuple relations and intersections are polynomially bounded, as are the number of tree edges and passes. Thus both query truth values and their difference are checkable in polynomial time. Nondeterministically guess the bounded database and verify these conditions, proving membership in NP. QED.

The membership proof assumes the *normalized* query hypergraphs are alpha-acyclic. It does not assume that chasing preserves that property. It evaluates the original queries on a guessed database, not arbitrary chased queries by an acyclic-query algorithm. This distinction avoids an invalid complexity inference.

## Corollary H4: state minimization and witness minimization are separate

Give P_G an FK-joined copy P_G and C(x_0), and give Q_false a distinct false copy. Insert the four query texts in the running eight-state workload. For every G and every subset of secondary keys, the quotient has four states with the same transition structure and the same pattern of two semantic outputs. Nonetheless its separating databases have the graph-dependent optimum of Theorem H2. Even a rigid canonical source core and a trivial fixed state quotient do not determine the globally smallest witness by retraction or state minimization.

The original query text grows with the graph. The theorem does not claim NP-hardness for a fixed finite catalogue, does not claim an approximation lower bound after an additive offset, and does not claim an efficient general algorithm for the chromatic number.

## Proposition H5: minimum databases need not be isomorphic

For the graph on four vertices with edges (0,1) and (2,3), beta=7 and chi=2, so the optimum is nine tuples. Let a,b be two distinct fresh integers. The color assignments (a,b,a,b) and (a,b,b,a) both construct minimum legal databases. In the first database, the unique tuple of T_1 is (b,a), with unequal coordinates; in the second it is (b,b), with equal coordinates. Any relational isomorphism preserves the name T_1 and equality of tuple coordinates. Therefore these two minimum databases are not isomorphic, even if arbitrary renaming of fresh integers is allowed. QED.

This contrasts with uniqueness of the minimum deterministic quotient up to isomorphism. One minimum is a behavioral state object; the other minimizes legal relational data. Neither uniqueness theorem transfers to the other object without proof.
