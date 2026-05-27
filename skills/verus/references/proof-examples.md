# Verus proof examples

Three worked patterns: canonicalisation of an unordered pair, an
inductive concat lemma over `Seq`, and the total-ordering composition
skeleton. They are intentionally generic — adapt the names to the
production module being mirrored.

## Canonicalisation: ordering an unordered pair

A common pattern is normalising an edge or pair so the smaller endpoint
is stored first. The spec function is total and the lemma is trivial,
but it sets up the spec types the rest of the proofs depend on.

```rust
use vstd::prelude::*;

verus! {

pub type ItemId = nat;
pub type Distance = int;
pub type Sequence = nat;

pub struct EdgeSpec {
    pub source: ItemId,
    pub target: ItemId,
    pub distance: Distance,
    pub sequence: Sequence,
}

impl EdgeSpec {
    pub open spec fn canonicalise(self) -> Self {
        if self.source <= self.target {
            self
        } else {
            EdgeSpec {
                source: self.target,
                target: self.source,
                distance: self.distance,
                sequence: self.sequence,
            }
        }
    }
}

proof fn lemma_canonicalise_is_ordered(e: EdgeSpec)
    ensures e.canonicalise().source <= e.canonicalise().target,
{
    // Z3 discharges by case split on e.source <= e.target.
}

} // verus!
```

## Inductive proof over a `Seq`

When proving that a property is preserved as edges are prepended or
concatenated, do the induction explicitly with `decreases` and call a
glue lemma that closes the inductive step. The `broadcast use` line is
required whenever the proof manipulates sequences with `add`, `push`, or
indexing across concatenations.

```rust
verus! {

pub open spec fn edges_invariant(
    edges: Seq<EdgeSpec>,
    source: ItemId,
) -> bool {
    forall|i: int| #![auto]
        0 <= i < edges.len() ==>
            edges[i].source == source && edges[i].target != source
}

proof fn lemma_concat_preserves_invariant(
    head: Seq<EdgeSpec>,
    tail: Seq<EdgeSpec>,
    source: ItemId,
)
    requires
        edges_invariant(head, source),
        edges_invariant(tail, source),
    ensures
        edges_invariant(head.add(tail), source),
{
    broadcast use vstd::seq::group_seq_axioms;

    let combined = head.add(tail);
    assert forall|i: int| #![auto]
        0 <= i < combined.len() implies
            combined[i].source == source && combined[i].target != source
    by {
        if i < head.len() {
            assert(combined[i] == head[i]);
        } else {
            let j = i - head.len();
            assert(combined[i] == tail[j]);
        }
    }
}

proof fn lemma_extract_invariant(items: Seq<EdgeSpec>, source: ItemId)
    requires forall|i: int| #![auto]
        0 <= i < items.len() ==>
            items[i].source == source && items[i].target != source,
    ensures edges_invariant(items, source),
    decreases items.len(),
{
    if items.len() == 0 {
        // Base: empty sequence satisfies the forall vacuously.
    } else {
        let rest = items.drop_first();
        lemma_extract_invariant(rest, source);
        // Concat lemma closes the inductive step:
        let prefix = Seq::<EdgeSpec>::empty().push(items.first());
        lemma_concat_preserves_invariant(prefix, rest, source);
    }
}

} // verus!
```

## Total-ordering composition

`vstd::relations::total_ordering` is opaque; reveal it before composing
the four sub-lemmas (reflexive, antisymmetric, transitive, strongly
connected). Each sub-lemma is small and case-splits over the comparator
chain.

```rust
verus! {

pub open spec fn edge_leq(a: EdgeSpec, b: EdgeSpec) -> bool {
    if a.distance < b.distance { true }
    else if a.distance > b.distance { false }
    else if a.source < b.source { true }
    else if a.source > b.source { false }
    else if a.target < b.target { true }
    else if a.target > b.target { false }
    else { a.sequence <= b.sequence }
}

proof fn lemma_edge_leq_reflexive() {
    assert forall|a: EdgeSpec| edge_leq(a, a) by { /* trivial */ }
}

// ... antisymmetric, transitive, strongly_connected lemmas follow the
// same case-split shape as the comparator chain above.

proof fn lemma_edge_leq_total_ordering()
    ensures total_ordering(|a: EdgeSpec, b: EdgeSpec| edge_leq(a, b)),
{
    reveal(total_ordering);
    lemma_edge_leq_reflexive();
    lemma_edge_leq_antisymmetric();
    lemma_edge_leq_transitive();
    lemma_edge_leq_strongly_connected();
}

} // verus!
```

Once `lemma_edge_leq_total_ordering` is in scope, downstream proofs can
invoke `edges.lemma_sort_by_ensures(...)` to obtain a sorted-multiset
guarantee for `edges.sort_by(edge_leq)` without re-deriving the
comparator properties at each call site.

## Cross-references

- [`verus-proof-example.rs`](verus-proof-example.rs) for the full
  project-layout view (root file, sub-files, `mod` declarations).
- [`../SKILL.md`](../SKILL.md) for trigger discipline, `assert by`,
  nonlinear arithmetic, and the broader catalogue of hard-won lessons.
