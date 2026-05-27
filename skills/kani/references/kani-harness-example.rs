//! Kani harness structure reference.
//!
//! Demonstrates the four-phase harness pattern (setup; nondeterministic
//! population; precondition enforcement; invariant assertion) plus helper
//! conventions. Included for reference only; the file is not compiled by
//! `rustc`. Harnesses are gated behind `#[cfg(kani)]` and executed via
//! `cargo kani`.
//!
//! Pairs with `skills/kani/SKILL.md` and
//! `skills/kani/references/harness-examples.md`.

// ---------------------------------------------------------------------------
// Cargo.toml: declare kani as a valid cfg
// ---------------------------------------------------------------------------
//
// [lints.rust]
// unexpected_cfgs = { level = "warn", check-cfg = ["cfg(kani)"] }

// ---------------------------------------------------------------------------
// Module declaration: conditionally compile the harness module
// ---------------------------------------------------------------------------
//
// In src/graph/mod.rs:
//
// #[cfg(kani)]
// mod kani_proofs;

// ---------------------------------------------------------------------------
// Makefile targets
// ---------------------------------------------------------------------------
//
// kani: ## Run practical Kani harnesses (fast feedback)
//     cargo kani -p my-crate --default-unwind 4 \
//         --harness verify_bidirectional_smoke_2_nodes
//     cargo kani -p my-crate --default-unwind 4 \
//         --harness verify_reverse_edge_reconciliation_2_nodes
//
// kani-full: ## Run all Kani harnesses (slow, nightly CI)
//     cargo kani -p my-crate --default-unwind 10

// ---------------------------------------------------------------------------
// Harness: deterministic smoke test
// ---------------------------------------------------------------------------

#[cfg(kani)]
#[kani::proof]
#[kani::unwind(4)]
fn verify_bidirectional_smoke_2_nodes() {
    // Phase 1: Deterministic setup
    let mut graph = Graph::with_capacity(2);

    graph
        .insert_first(NodeContext { node: 0 })
        .expect("insert node 0");
    graph
        .attach_node(NodeContext { node: 1 })
        .expect("attach node 1");

    // Phase 2: Deterministic edge population
    add_bidirectional_edge(&mut graph, 0, 1);

    // Phase 3: No assumptions needed (deterministic setup)

    // Phase 4: Assert the invariant
    kani::assert(
        is_bidirectional(&graph),
        "bidirectional invariant violated in smoke harness",
    );
}

// ---------------------------------------------------------------------------
// Harness: nondeterministic reconciliation
// ---------------------------------------------------------------------------

#[cfg(kani)]
#[kani::proof]
#[kani::unwind(4)]
fn verify_reverse_edge_reconciliation_2_nodes() {
    // Phase 1: Deterministic setup
    let mut graph = Graph::with_capacity(2);

    graph
        .insert_first(NodeContext { node: 0 })
        .expect("insert node 0");
    graph
        .attach_node(NodeContext { node: 1 })
        .expect("attach node 1");

    // Phase 2: Nondeterministic population
    let should_link = kani::any::<bool>();
    if should_link {
        add_edge_if_missing(&mut graph, 0, 1);

        // Phase 3: Exercise production reconciliation code
        let added = ensure_reverse_edge(&mut graph, 0, 1);
        kani::assert(added, "expected reverse edge to be inserted");
    }

    // Phase 4: Assert the invariant
    kani::assert(
        is_bidirectional(&graph),
        "bidirectional invariant violated after reconciliation",
    );
}

// ---------------------------------------------------------------------------
// Harness: eviction and deferred cleanup
// ---------------------------------------------------------------------------

#[cfg(kani)]
#[kani::proof]
#[kani::unwind(10)]
fn verify_eviction_deferred_cleanup() {
    // Phase 1: Setup (4-node graph, single capacity slot)
    let mut graph = setup_eviction_test_graph();

    // Phase 2: Seed node 1 at capacity
    add_edge_if_missing(&mut graph, 1, 2);
    add_edge_if_missing(&mut graph, 2, 1);

    // Phase 3: Drive production commit-path code
    apply_commit_updates(&mut graph, /* new_node */ 3, /* candidates */ &[1])
        .expect("commit-path updates must succeed");

    // Phase 4: Assert invariants (both positive and negative)
    kani::assert(
        is_bidirectional(&graph),
        "bidirectional invariant violated after eviction and deferred cleanup",
    );
    assert_link(&graph, 1, 0, "node 1 should link to node 0 after eviction");
    assert_no_link(&graph, 2, 1, "deferred cleanup should remove node 2's stale edge");
}

// ---------------------------------------------------------------------------
// Helper functions (gated behind #[cfg(kani)])
// ---------------------------------------------------------------------------

#[cfg(kani)]
fn setup_eviction_test_graph() -> Graph {
    let mut graph = Graph::with_capacity(4);
    graph.insert_first(NodeContext { node: 0 }).expect("insert node 0");
    graph.attach_node(NodeContext { node: 1 }).expect("attach node 1");
    graph.attach_node(NodeContext { node: 2 }).expect("attach node 2");
    graph.attach_node(NodeContext { node: 3 }).expect("attach node 3");
    graph
}

#[cfg(kani)]
fn assert_link(graph: &Graph, src: usize, dst: usize, message: &str) {
    let has_link = graph
        .node(src)
        .map(|n| n.neighbours().contains(&dst))
        .unwrap_or(false);
    kani::assert(has_link, message);
}

#[cfg(kani)]
fn assert_no_link(graph: &Graph, src: usize, dst: usize, message: &str) {
    let has_link = graph
        .node(src)
        .map(|n| n.neighbours().contains(&dst))
        .unwrap_or(false);
    kani::assert(!has_link, message);
}

#[cfg(kani)]
fn add_bidirectional_edge(graph: &mut Graph, origin: usize, target: usize) {
    add_edge_if_missing(graph, origin, target);
    add_edge_if_missing(graph, target, origin);
}
