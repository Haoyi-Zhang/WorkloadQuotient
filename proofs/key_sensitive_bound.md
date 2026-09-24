# Exact key-sensitive witness growth and a rigid-core gap

## The permutation cascade

Fix depth d>=1. Relation R0 has attributes (id,a,b) and key id. For 1<=i<=d, relation Ri has attributes (id,parent,a,b) and key (parent,a,b). Choose any H subset of {1,...,d}; declare id an additional key of Ri precisely when i belongs to H. The two keys are incomparable position sets. The additional key is never the target of an FK.

For every i<d, there are two FKs from Ri to the key (parent,a,b) of R_(i+1). For R0 their source lists are (id,a,b) and (id,b,a); for later relations they are the positions carrying the same named attributes. Thus every tuple with identifier z and orientation (a,b) forces a child tuple with target key (z,a,b) and a child tuple with target key (z,b,a). The FK relation graph is a chain with two parallel edges per step. The maximum arity is four.

Let p_plus(k) be R0(k,0,1), and p_minus(k) be R0(k,1,0). They are one-atom acyclic queries. An optional syntactic copy joins the first forced child in orientation (0,1), respectively (1,0), without exposing its identifier; each copy is equivalent to its original by the relevant FK.

Define N0=1 and, for i>=1,

    Ni = 2*N_(i-1)  if i=1 or i-1 belongs to H,
    Ni = 2          otherwise.

Let L(d,H)=sum_(i=0)^d Ni.

## Theorem K1: exact global minimum

Among all finite legal databases D on which p_plus(D) differs from p_minus(D), the smallest possible total number of tuples is exactly L(d,H). The same bound holds in either directed difference separately.

**Lower bound.** Any difference contains an output k present in one query and absent from the other. It forces a root tuple with one of the two orientations. The key on R0.id prevents the opposite root tuple for that same identifier. We may follow only the FK witnesses forced by this root and disregard any extra tuples elsewhere; all followed orientations remain either (0,1) or (1,0).

At level one the root identifier forces two different target-key values, (k,0,1) and (k,1,0). They cannot be the same tuple because 0 and 1 are distinct. Thus at least two R1-tuples are required.

Suppose a selected set of forced tuples at level i-1 has size at least N_(i-1). If id is a key there, their identifiers are pairwise distinct. Each identifier forces two child target keys, and target keys belonging to distinct parent identifiers are also distinct. At least 2*N_(i-1) child tuples therefore exist. If id is not a key, at least one parent identifier still exists, and it forces the two orientations, so at least two child tuples exist. These are exactly the two recurrence cases. This argument counts only tuples reachable from the selected root; arbitrary additional database tuples cannot reduce any lower bound. Summing the per-relation lower bounds gives |D|>=L(d,H). The proof is invariant under exchanging the two root orientations.

**Matching construction.** Use one root tuple (2,0,1). For every next level, form exactly the required keys (z,0,1) and (z,1,0) for the distinct identifiers z at the preceding level. If the new level's id key is declared, assign a distinct identifier to every required tuple; otherwise give every tuple the same identifier 2. The target key (parent,a,b) holds because only one tuple is created per required key. The extra identifier key holds exactly at the levels where distinct identifiers were assigned. Every FK holds by construction. The number of distinct parent identifiers is the number of parent tuples when that level has the identifier key, and one otherwise, giving exactly the recurrence. The root query p_plus returns 2 and p_minus does not. Exchanging 0 and 1 gives the opposite directed witness. QED.

## Corollaries and boundaries

When H is empty, Ni=2 for every positive level and L(d,empty)=1+2d. When every positive level has its identifier key, Ni=2^i and L(d,H)=2^(d+1)-1. A key on the terminal relation's id cannot affect the tuple count because no FK leaves that relation, although it changes which identifier assignments are legal.

With d=7 there are eight relation symbols, arity at most four, and two one-atom output queries, yet every distinguishing database has at least 255 tuples. Thus a 128-tuple execution cap cannot establish universal equivalence by failed search even inside these otherwise small dimensions. This is an exact mathematical lower bound, not an inference from unsuccessful enumeration. The artifact computes this formula and refuses to materialize an over-cap instance; it never produces a 255-tuple experimental database.

## Theorem K2: the universal source chase is a rigid core

For every H, the normalized chase C_plus of p_plus has exactly 2^(d+1)-1 facts and has only the identity endomorphism when written constants are fixed. Consequently it has no proper retract and is a core, even when H is empty.

**Proof of size.** Before identifications, the root creates two children, each creates two children, and so forth. The identifier of each newly created child is fresh. Within each level, the key (parent,a,b) distinguishes children of different parents and the two orientations of one parent. The optional identifier key never equates two fresh identifiers. Therefore no key forces two different chase tuples to coincide. The tree has 2^i tuples at level i and their sum is the stated number.

**Proof of rigidity.** There is exactly one R0-tuple. Any endomorphism must map it to itself, fixing its identifier and its two constants. Assume all identifiers and orientations at level i-1 are fixed. A child at level i has key (z,a,b), and all three of these terms are fixed. The instance contains exactly one tuple of Ri with this key, so the endomorphism must send that tuple to itself, fixing its identifier as well. Induction fixes every term occurring in the chase. Thus every endomorphism is the identity. A retraction onto a proper subinstance would be a nonidentity endomorphism or would omit a fact whose fixed image must remain; neither is possible. QED.

This statement concerns the source universal instance, not arbitrary input databases. It also concerns ordinary finite relational cores; it does not rely on a special algorithm that merely happens to miss a smaller retract.

## Corollary K3: cores and minimum legal countermodels can differ exponentially

For H empty, the canonical source instance is already a rigid core with 2^(d+1)-1 tuples, while a globally smallest distinguishing database has 1+2d tuples. Their ratio is (2^(d+1)-1)/(2d+1), exponential up to its linear divisor.

The smaller witness is a homomorphic image of the larger one: it identifies identifiers within each keyless level. It is not a retract or a subinstance of that source chase. In particular, the id of a child and a parent can be interpreted by the same integer in the smaller model even though the source chase used different fresh names. All keys and FKs remain legal. An image must still be tested for legality in general; the existence of these legal identifications does not say that every identification is valid.

## Corollary K4: a constant semantic state quotient does not bound witness size

Insert the plus/minus queries and their FK-joined copies into the eight-state running workload of Theorem Q3's example. For every d and H it has exactly four reachable semantic classes, two present-output classes, and eight literal-label classes. The FK-joined copies remain equivalent under every H, and the root query pair remains distinguishable by Theorem K1. Therefore adding or removing the auxiliary identifier keys changes the intrinsic countermodel size but not the quotient of this particular workload.

This is not a statement that the schema changes preserve equivalence of every possible query. It is not a claim that small quotients are computationally hard to construct on these examples: their quotient is elementary. The separation is precisely between the amount of state retained and the unavoidable size of the legal evidence explaining a difference.

## Certificate size versus raw construction records

A root-query unfolding has 2^(d+1)-1 records. Starting instead from the root and its explicit first-child atom unfolds both seeds and creates (2^(d+1)-1)+(2^d-1)=3*2^d-2 records. Key saturation identifies the explicit child and its descendants with the corresponding forced branch, so the final normalized facts are still the root chase. At d=6 these numbers are 127 and 190. A raw derivation record is not an extra database tuple, and the artifact reports both quantities separately.
