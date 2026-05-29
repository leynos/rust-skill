# Kani harness examples

Two worked harnesses, with the four-phase pattern flagged. Both target a
graph with bidirectional links; the same shape transfers to any data
structure that maintains a paired invariant.

## Smoke test (deterministic)

A deterministic smoke test is the first thing to write for a new harness.
It exercises the production code on a known input and proves that the
harness, helpers, and `is_bidirectional` predicate agree before any
symbolic exploration is added.

```rust
#[cfg(kani)]
#[kani::proof]
#[kani::unwind(4)]
fn verify_bidirectional_smoke_2_nodes() {
    // Phase 1: deterministic setup.
    let mut graph = Graph::with_capacity(2);
    graph.insert_first(NodeContext { node: 0 }).expect("insert");
    graph.attach_node(NodeContext { node: 1 }).expect("attach");

    // Phase 2: deterministic population (no kani::any here).
    add_bidirectional_edge(&mut graph, 0, 1);

    // Phase 3: no assumptions needed; setup is fully concrete.

    // Phase 4: assert.
    kani::assert(is_bidirectional(&graph), "invariant violated");
}
```

## Reconciliation (nondeterministic)

This harness adds a single nondeterministic decision (whether to seed the
forward edge), then drives the real production reconciliation function
and asserts the invariant.

```rust
#[cfg(kani)]
#[kani::proof]
#[kani::unwind(4)]
fn verify_reverse_edge_reconciliation_2_nodes() {
    let mut graph = Graph::with_capacity(2);
    graph.insert_first(NodeContext { node: 0 }).expect("insert");
    graph.attach_node(NodeContext { node: 1 }).expect("attach");

    let should_link = kani::any::<bool>();
    if should_link {
        add_edge_if_missing(&mut graph, 0, 1);
        let added = ensure_reverse_edge(&mut graph, 0, 1);
        kani::assert(added, "expected reverse edge to be inserted");
    }

    kani::assert(is_bidirectional(&graph), "invariant violated");
}
```

## Eviction cascade

A more involved harness that drives a commit-path routine which can evict
an existing edge and trigger a deferred clean-up. Verifies a positive
invariant (new edge exists) and a negative one (the evicted edge is gone)
on the same final state.

```rust
#[cfg(kani)]
#[kani::proof]
#[kani::unwind(10)]
fn verify_eviction_deferred_cleanup() {
    let mut graph = setup_eviction_test_graph();

    // Seed node 1 at capacity with node 2.
    add_edge_if_missing(&mut graph, 1, 2);
    add_edge_if_missing(&mut graph, 2, 1);

    // Apply an update: node 0 adds node 1 as a neighbour. This must evict
    // node 2 and stage a deferred cleanup of node 2's stale forward edge.
    apply_commit_updates(&mut graph, /* new_node */ 3, /* candidates */ &[1])
        .expect("commit-path updates must succeed");

    kani::assert(is_bidirectional(&graph), "invariant violated");
    assert_link(&graph, 1, 0, "node 1 should link to node 0 after eviction");
    assert_no_link(&graph, 2, 1, "deferred cleanup should remove the stale edge");
}
```

## Helper patterns

Keep helpers in the same `#[cfg(kani)]` module as the harnesses. They
should be small and named after the production assertion they paraphrase:

```rust
#[cfg(kani)]
fn assert_link(graph: &Graph, src: usize, dst: usize, msg: &str) {
    let has = graph
        .node(src)
        .map(|n| n.neighbours().contains(&dst))
        .unwrap_or(false);
    kani::assert(has, msg);
}

#[cfg(kani)]
fn assert_no_link(graph: &Graph, src: usize, dst: usize, msg: &str) {
    let has = graph
        .node(src)
        .map(|n| n.neighbours().contains(&dst))
        .unwrap_or(false);
    kani::assert(!has, msg);
}
```

Bundle multi-step setup behind a helper too. `setup_eviction_test_graph`
above hides the four-node, single-level construction so the harness body
reads as the scenario, not the bookkeeping.
