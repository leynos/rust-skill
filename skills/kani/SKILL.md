---
name: kani
description: Write and maintain Kani bounded model checking harnesses for Rust. Use when verifying structural invariants, unsafe code, bounded state machines, or dispatch logic via exhaustive symbolic execution.
---

# Kani bounded model checking for Rust

Kani uses the CBMC (C Bounded Model Checker) backend to explore every
execution path within stated bounds, providing formal guarantees rather than
probabilistic coverage. Load the `rust-verification` skill first for the
selection rules; load this skill once Kani is the chosen tool.

## When to apply

Apply when:

- structural invariants (bidirectional links, uniqueness, ordering,
  reachability) must hold,
- `unsafe` code needs exhaustive coverage of undefined behaviour,
- bounded state machines, dispatch selectors, or parser-like logic need
  verification,
- a property test should be complemented with exhaustive bounded
  exploration.

Do not apply when the property requires unbounded induction (use Verus),
the code is concurrency-heavy (Kani sequentialises atomics and
thread-locals), the code is dominated by I/O, or a unit or property test
would suffice.

## Installation

Use [`rust-prover-tools`](https://github.com/leynos/rust-prover-tools) as
the canonical installer and version pin:

```bash
prover-tools kani install
prover-tools kani check-version
```

`install` runs `cargo install --locked kani-verifier` against the pinned
version, then `cargo kani setup`. `check-version` confirms the running
Kani matches the pin. For one-off use without a pin, the upstream route
remains `cargo install --locked kani-verifier && cargo kani setup`. See
[`references/installation-note.md`](references/installation-note.md) for
the rationale and the version-file convention.

## Core concepts

A Kani harness is a function annotated with `#[kani::proof]`. It runs
under symbolic inputs:

- `kani::any::<T>()` produces a symbolic value covering every bit pattern
  for `T`. Derive `kani::Arbitrary` for custom types.
- `kani::assume(cond)` constrains the search to states the production
  code can actually reach. Only use it to mirror real preconditions.
- `kani::assert(cond, msg)` is the property under verification. Any input
  satisfying the assumptions that violates the assertion is reported as a
  counter-example.
- `#[kani::unwind(n)]` bounds loop iterations. The bound must be **one
  greater** than the maximum number of iterations.

Each harness follows four phases: deterministic setup, nondeterministic
population, precondition enforcement, invariant assertion.

## A good harness

This harness exercises a production reconciliation routine and verifies a
bidirectional-link invariant on a 2-node graph:

```rust
#[kani::proof]
#[kani::unwind(4)]
fn verify_reverse_edge_reconciliation_2_nodes() {
    let mut graph = Graph::with_capacity(2);
    graph.insert_first(NodeContext { node: 0 }).expect("insert");
    graph.attach_node(NodeContext { node: 1 }).expect("attach");

    let should_link = kani::any::<bool>();
    if should_link {
        add_edge_if_missing(&mut graph, 0, 1);
        // Drive the real production reconciliation function.
        let added = ensure_reverse_edge(&mut graph, 0, 1);
        kani::assert(added, "expected reverse edge to be inserted");
    }

    kani::assert(is_bidirectional(&graph), "invariant violated");
}
```

The harness drives the production function rather than a re-implementation;
the unwind bound is tight; assertions check an externally meaningful
invariant. See
[`references/harness-examples.md`](references/harness-examples.md) for two
worked harnesses (smoke and eviction-cascade) plus their helpers.

## Anti-patterns

- **The harness re-implements the invariant.** Manually inserting the
  reverse edge before asserting bidirectionality proves the harness, not
  the production code. A mutation test on the production code will pass.
- **Over-constrained assumptions.** `kani::assume(x == 42)` collapses the
  search to a single input. Use `cargo kani --coverage -Z source-coverage`
  to detect coverage gaps inside the assumed region.
- **Excessive unwind.** Unwind bounds far above the true loop count waste
  solver time. Start tight; grow only when an `unwinding assertion`
  failure forces it.

## What Kani detects and what it does not

Detects: panics (including `unwrap` on `None` and out-of-bounds), debug
arithmetic overflow, null-pointer dereferences in `unsafe`, assertion
failures, undefined behaviour in `unsafe` blocks, bit-shift overflow.

Does not model: concurrency (atomics and thread-locals are treated as
sequential — do not use Kani for data-race detection), I/O, unbounded heap
collections (manual bounds required), async, and floating-point precision
(use stubs for trig and `sqrt`).

## Project integration

- Gate all harness code behind `#[cfg(kani)]` and declare the cfg in
  `Cargo.toml`:

  ```toml
  [lints.rust]
  unexpected_cfgs = { level = "warn", check-cfg = ["cfg(kani)"] }
  ```

- Split harness runs into two tiers: a fast `make kani` for the local
  loop and a slow `make kani-full` for nightly CI. Keep Kani out of
  `make test`.
- Validate every harness with a one-off mutation: break the production
  code, confirm the harness fails with a meaningful message, then restore.
  A harness that still passes after a deliberate mutation is not testing
  what it claims to test.

## Function contracts (experimental)

Kani's `#[kani::requires]` and `#[kani::ensures]` allow compositional
verification:

```rust
#[kani::requires(divisor != 0)]
#[kani::ensures(|r| *r <= dividend)]
fn safe_div(dividend: u32, divisor: u32) -> u32 { dividend / divisor }

#[kani::proof_for_contract(safe_div)]
fn verify_safe_div() { safe_div(kani::any(), kani::any()); }
```

Run with `cargo kani -Z function-contracts`. Use
`#[kani::stub_verified(name)]` elsewhere to replace verified functions
with their contracts and cut solver load.

## Hard-won lessons

- Unwind bounds are off-by-one (a 10-iteration loop needs `unwind(11)`).
- Heap collections do not scale: even 2-element `Vec`s can take minutes;
  3-element ones often time out. There is a sharp combinatorial cliff
  between 2-node and 3-node harnesses for graph problems.
- Compilation is slow: 30–60 seconds before verification even starts.
- Solver choice matters: `#[kani::solver(kissat)]` or `cadical` can turn
  a timeout into a sub-minute proof.
- Stubs let Kani run against code with FFI, inline assembly, or RNG calls:

  ```rust
  #[cfg(kani)]
  fn mock_random<T: kani::Arbitrary>() -> T { kani::any() }

  #[kani::proof]
  #[kani::stub(rand::random, mock_random)]
  fn verify_with_random() { let _: u32 = rand::random(); }
  ```

  Run with `cargo kani -Z stubbing`.

## References

- [Kani Rust Verifier](https://github.com/model-checking/kani) and
  [documentation](https://model-checking.github.io/kani/).
- [Tutorial: First Steps](https://model-checking.github.io/kani/tutorial-first-steps.html),
  [Attributes Reference](https://model-checking.github.io/kani/reference/attributes.html),
  [Stubbing](https://model-checking.github.io/kani/reference/experimental/stubbing.html),
  [Function Contracts](https://model-checking.github.io/kani/reference/experimental/contracts.html),
  [Rust Feature Support](https://model-checking.github.io/kani/rust-feature-support.html).
- [`references/harness-examples.md`](references/harness-examples.md) for
  worked harnesses with helpers.
- [`references/kani-harness-example.rs`](references/kani-harness-example.rs)
  for a self-contained Rust source illustrating the four-phase shape.
