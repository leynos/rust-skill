//! Verus proof structure reference.
//!
//! Demonstrates the project layout, spec type patterns, and lemma
//! composition approach for a small ordering-and-extraction proof. The
//! example is a sequence-of-edges proof that mirrors a production
//! `EdgeSet` module, with neutral names so the shape is the focus.
//!
//! This file is included for reference and is not compiled by `rustc`;
//! it is run with the Verus toolchain via
//! `prover-tools verus run --proof-file verus/my_proofs.rs`.
//!
//! Pairs with `skills/verus/SKILL.md` and
//! `skills/verus/references/proof-examples.md`.

// ---------------------------------------------------------------------------
// Project layout
// ---------------------------------------------------------------------------
//
// project/
// ├── verus/
// │   ├── my_proofs.rs            # Root: types, specs, top-level lemmas
// │   ├── my_proofs_extract.rs    # Extraction invariant proofs
// │   └── my_proofs_ordering.rs   # Ordering property proofs
// └── tools/
//     └── verus/
//         ├── VERSION             # e.g., 0.2026.01.30.<commit>
//         └── SHA256SUMS

// ---------------------------------------------------------------------------
// Root proof file: types, specifications, and top-level lemmas
// ---------------------------------------------------------------------------

use vstd::prelude::*;
use vstd::relations::sorted_by;
use vstd::seq_lib::*;

mod my_proofs_extract;
mod my_proofs_ordering;

fn main() {}

verus! {

// -- Spec type aliases (mirror production types) ----------------------------

/// Identifier for an item participating in the relation.
pub type ItemId = nat;
/// Monotonic insertion sequence number for candidate edges.
pub type Sequence = nat;
/// Distance metric value used for ordering edges.
pub type Distance = int;

// -- Spec structs (mirror production structs) -------------------------------

pub struct ItemSpec {
    pub id: ItemId,
    pub distance: Distance,
}

pub struct SegmentSpec {
    pub items: Seq<ItemSpec>,
}

pub struct ExtractionPlanSpec {
    pub segments: Seq<SegmentSpec>,
}

pub struct EdgeSpec {
    pub source: ItemId,
    pub target: ItemId,
    pub distance: Distance,
    pub sequence: Sequence,
}

// -- Spec functions (pure specifications) -----------------------------------

impl EdgeSpec {
    /// Returns a canonical edge with ordered endpoints.
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

/// Total ordering on edges: distance, then source, target, sequence.
pub open spec fn edge_leq(a: EdgeSpec, b: EdgeSpec) -> bool {
    if a.distance < b.distance { true }
    else if a.distance > b.distance { false }
    else if a.source < b.source { true }
    else if a.source > b.source { false }
    else if a.target < b.target { true }
    else if a.target > b.target { false }
    else { a.sequence <= b.sequence }
}

/// Counts items whose id differs from `source_item` (recursive, with
/// `decreases` clause).
pub open spec fn count_non_self(
    items: Seq<ItemSpec>,
    source_item: ItemId,
) -> nat
    decreases items.len(),
{
    if items.len() == 0 {
        0
    } else {
        let head = items.first();
        let rest = items.drop_first();
        if head.id == source_item {
            count_non_self(rest, source_item)
        } else {
            1 + count_non_self(rest, source_item)
        }
    }
}

// -- Invariant specifications -----------------------------------------------

/// Shared invariants: correct length, all edges have expected source,
/// no self-edges, correct sequence number.
pub open spec fn edges_common_invariants(
    edges: Seq<EdgeSpec>,
    expected_len: nat,
    source_item: ItemId,
    source_sequence: Sequence,
) -> bool {
    // Note the use of #![auto] for trigger selection:
    &&& edges.len() == expected_len
    &&& forall|i: int| #![auto] 0 <= i < edges.len() ==> edges[i].source == source_item
    &&& forall|i: int| #![auto] 0 <= i < edges.len() ==> edges[i].target != source_item
    &&& forall|i: int| #![auto] 0 <= i < edges.len() ==> edges[i].sequence == source_sequence
}

// -- Top-level proof (composes sub-lemmas) ----------------------------------

/// Proves that sorting edges by `edge_leq` preserves the multiset and
/// produces a sorted sequence.
proof fn lemma_extract_from_unsorted_invariants(edges: Seq<EdgeSpec>)
    ensures
        extract_invariants(edges),
{
    // Compose: first prove total ordering, then invoke the sort lemma.
    my_proofs_ordering::lemma_edge_leq_total_ordering();
    edges.lemma_sort_by_ensures(|a: EdgeSpec, b: EdgeSpec| edge_leq(a, b));
}

} // verus!

// ---------------------------------------------------------------------------
// Sub-proof file: extraction invariants (my_proofs_extract.rs)
// ---------------------------------------------------------------------------
//
// Key patterns demonstrated:
// - Inductive proof over Seq (base case + recursive step)
// - Helper lemma for prepend-preserves-invariants
// - Helper lemma for concat-preserves-invariants
// - broadcast use group_seq_axioms for sequence axioms
//
// verus! {
// use super::*;
//
// proof fn lemma_prepend_first_edge_preserves_common_invariants(
//     first_edge: EdgeSpec,
//     rest_edges: Seq<EdgeSpec>,
//     rest_expected: nat,
//     source_item: ItemId,
//     source_sequence: Sequence,
// )
//     requires
//         edges_common_invariants(rest_edges, rest_expected, source_item, source_sequence),
//         first_edge.source == source_item,
//         first_edge.target != source_item,
//         first_edge.sequence == source_sequence,
//     ensures
//         edges_common_invariants(
//             Seq::<EdgeSpec>::empty().push(first_edge).add(rest_edges),
//             1 + rest_expected,
//             source_item,
//             source_sequence,
//         ),
// {
//     broadcast use vstd::seq::group_seq_axioms;
//
//     let prefix = Seq::<EdgeSpec>::empty().push(first_edge);
//     let edges = prefix.add(rest_edges);
//
//     // Prove each conjunct separately with explicit index reasoning:
//     assert forall|i: int| #![auto] 0 <= i < edges.len()
//         implies edges[i].source == source_item
//     by {
//         if i == 0 {
//             assert(edges[i] == prefix[i]);
//         } else {
//             let j = i - 1;
//             assert(edges[i] == rest_edges[j]);
//         }
//     }
//     // (Similar blocks for .target and .sequence)
// }
// } // verus!

// ---------------------------------------------------------------------------
// Sub-proof file: ordering properties (my_proofs_ordering.rs)
// ---------------------------------------------------------------------------
//
// Key patterns demonstrated:
// - Proving reflexivity, antisymmetry, transitivity, strong connectedness
// - Composing into total_ordering via reveal()
// - Case-split proof structure matching the function's if-else chain
//
// verus! {
// use super::*;
//
// proof fn lemma_edge_leq_total_ordering()
//     ensures
//         total_ordering(|a: EdgeSpec, b: EdgeSpec| edge_leq(a, b)),
// {
//     reveal(total_ordering);  // Must reveal opaque vstd definition
//     lemma_edge_leq_reflexive();
//     lemma_edge_leq_antisymmetric();
//     lemma_edge_leq_transitive();
//     lemma_edge_leq_strongly_connected();
// }
// } // verus!
