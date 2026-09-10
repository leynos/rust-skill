---
name: kani
description: Write and maintain Kani bounded model checking harnesses for Rust. Use when verifying structural invariants, unsafe code, bounded state machines, or dispatch logic via exhaustive symbolic execution, and when wiring Kani into a repository through rust-prover-tools.
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
- `unsafe` code needs exhaustive coverage of undefined behaviour
  (`from_utf8_unchecked`, lifetime-extending `transmute`, `Send + Sync`
  claims, index or drain arithmetic whose safety rests on an external
  invariant),
- bounded state machines, dispatch selectors, or parser-like logic need
  verification,
- a property test should be complemented with exhaustive bounded
  exploration.

Do not apply when the property requires unbounded induction (use Verus),
the code is concurrency-heavy (Kani sequentialises atomics and
thread-locals), the code crosses FFI into an embedded interpreter or real
syscalls (refactor to a pure state machine over an event enum first), the
type system already enforces the invariant, or a unit or property test
would suffice. Reviewers reject Kani in those cases as disproportionate.

A reviewer request for a harness must be answered one of three ways:
land it, defer it to a tracked issue with the reason, or decline it with a
written justification in the developers' guide. A bundled request
("proptest and Kani") is two items; track both.

## Installation and project wiring

Use [`rust-prover-tools`](https://github.com/leynos/rust-prover-tools) as
the canonical installer and version pin:

```bash
prover-tools kani install --repo-root .
prover-tools kani check-version --repo-root .
```

`install` runs `cargo install --locked kani-verifier --version <pin>`
against `tools/kani/VERSION`, then `cargo kani setup`. `check-version`
fails if the running Kani differs from the pin; run it before any proof.
`--locked` alone does not pin the verifier release.

The repository shape reviewers expect (pin files, `check-cfg`, Makefile
targets that delegate to `prover-tools`, a smoke and a nightly CI job,
contract tests, a harness inventory) is laid out step by step in
[`references/project-on-ramp.md`](references/project-on-ramp.md). See
[`references/installation-note.md`](references/installation-note.md) for
the rationale and the version-file convention.

## Core concepts

A Kani harness is a function annotated with `#[kani::proof]`. It runs
under symbolic inputs:

- `kani::any::<T>()` produces a symbolic value covering every bit pattern
  for `T`. Derive `kani::Arbitrary` for custom types.
- `kani::assume(cond)` constrains the search to states the production
  code can actually reach. Only use it to mirror real preconditions, and
  only at the harness's call site, never inside production code.
- `kani::assert(cond, msg)` is the property under verification. Any input
  satisfying the assumptions that violates the assertion is reported as a
  counter-example.
- `kani::cover!(cond)` records that a branch is reachable. Every branch
  the harness claims to exercise needs one; a harness that never reaches
  the interesting path is green and worthless.
- `#[kani::unwind(n)]` bounds loop iterations. The bound must be **one
  greater** than the maximum number of iterations. Prefer it on the
  harness over `--default-unwind` so the bound is visible and reviewed.

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
    kani::cover!(should_link, "linked path is reachable");

    kani::assert(is_bidirectional(&graph), "invariant violated");
}
```

The harness drives the production function rather than a re-implementation;
the unwind bound is tight; assertions check an externally meaningful
invariant through the same helper production uses. See
[`references/harness-examples.md`](references/harness-examples.md) for two
worked harnesses (smoke and eviction-cascade) plus their helpers.

## The review bar

These are the findings reviewers raise most often on harnesses; check
each before opening the PR. The full list with examples is in
[`references/review-failure-modes.md`](references/review-failure-modes.md).

- **The harness must drive production code.** No placeholder
  `kani::assert(true)`, no hand-written mirror, no constructing the
  expected value directly. If a Kani-only model is unavoidable, add an
  equivalence proof or exhaustive equivalence tests and record why.
- **No swallowed paths.** `if let Ok(x) = f()` and `unwrap_or(false)`
  before a negative assertion pass vacuously. Assert `Ok`/`Some` first;
  on an unexpected arm, `kani::assert(false, "reason")`.
- **Prove both directions.** "Every output traces to an input" is not
  "no output lacks an input".
- **Symbolic inputs match the claim.** A harness documented as covering
  all levels with `level` hardcoded to `0` overstates coverage.
- **Share the driver.** Put the routine that both proptest and Kani call
  under `#[cfg(any(test, kani))]` as `pub(crate)`; prefer production
  types over Kani-only twins.
- **Preconditions and bounds live at the call site**, typed, and
  documented as concrete numbers (N, alphabet, unwind), not "bounded".
- **Symbolic setup does not panic.** Deterministic setup on known-good
  inputs may use `.expect()`; setup that consumes symbolic or
  data-dependent values must not, because a panicking setup path defeats
  the harness instead of failing the obligation. Validate indices
  defensively.
- **Narrow the API instead of proving misuse harmless.**

## `cfg(kani)` is a different build

The normal gates do not compile harness code, so the following surface
only at review or in the nightly job unless you check them locally:

- unused imports and dead code under `cfg(kani)` survive `-D warnings`;
- Clippy's allow-`expect`-in-tests exemption does not apply;
- complexity, function-length, and argument-count thresholds apply to
  harness helpers;
- a call into a `cfg(test)`-only helper from shared code breaks every
  harness;
- `#[allow(dead_code)]` as a gating workaround is rejected; use scoped
  `#[expect(lint, reason = "...")]` or delete the wrapper;
- `cargo-mutants` ignores the cfg, so harness modules need an exclusion;
- Kani bundles its own nightly: `const fn` stability and borrow-check
  behaviour can differ from the workspace toolchain, and
  `RUSTUP_TOOLCHAIN` does not upgrade Kani.

Gate all harness code behind `#[cfg(kani)]` and declare the cfg:

```toml
[lints.rust]
unexpected_cfgs = { level = "warn", check-cfg = ["cfg(kani)"] }
```

## Solver cliffs and the "measured intractable" protocol

- Heap collections and strings dominate the proof budget: real
  `HashMap`, serde, hashing, and path types are lowered before the
  invariant is reached. Use fixed-size arrays, an explicit degree cap, or
  a bounded array with an O(n²) linear scan in place of a `HashSet`; keep
  a `cfg(kani)`-only compatibility collection private behind a `not(kani)`
  type alias.
- Extract a generic kernel and prove it over `u8` with a thin adapter
  harness; this turned an 8 GiB blow-up at N=3 into a 7.6 s proof.
- Nested loops need N² unwind. Recompute bounds after any refactor that
  changes traversal shape; bind bound literals to production constants
  with `const` assertions where the attribute allows it.
- Bounded inputs can exclude branches (overflow handling) that only fire
  outside the bound; add a smoke harness or document the gap.
- When a requested harness is intractable: measure it (timeout, aborted
  paths, memory), substitute an equivalence or unit-test proxy, open a
  tracked issue, and say so. Reviewers accept a measurement, not "too
  hard".

## What Kani detects and what it does not

Detects: panics (including `unwrap` on `None` and out-of-bounds), debug
arithmetic overflow, null-pointer dereferences in `unsafe`, assertion
failures, undefined behaviour in `unsafe` blocks, bit-shift overflow.

Does not model: concurrency (atomics and thread-locals are treated as
sequential — do not use Kani for data-race detection), I/O, unbounded heap
collections (manual bounds required), async, FFI into an embedded
interpreter, and floating-point precision (use stubs for trig and `sqrt`).

## Project integration

- Split harness runs into two tiers: a fast `make kani` of named
  harnesses for pull requests and a slow `make kani-full` for nightly CI.
  Keep Kani out of `make test` unless the repository has chosen a
  fail-closed formal gate and documented it.
- Keep a harness inventory table in the developers' guide (name, module,
  bounds, what is proved and what is not) and update it in the same PR as
  any harness change; reviewers treat partial documentation as a failing
  check. Keep ExecPlan status fields and quoted bounds in agreement with
  the code.
- Validate every harness with a one-off mutation: break the production
  code, confirm the harness fails with a meaningful message, then restore.
  Repositories with mutation-evidence tests require a committed patch per
  harness.

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
  between 2-node and 3-node harnesses for graph problems; `chutoro`
  retired its 3-node harness after it found a real ordering bug by hand
  tracing but never finished under CBMC.
- Compilation is slow: 30–60 seconds before verification even starts.
- Solver choice matters: `#[kani::solver(kissat)]` or `cadical` can turn
  a timeout into a sub-minute proof; a code-health refactor can also push
  a formula past the solver's variable-index limit.
- Stubs let Kani run against code with FFI, inline assembly, or RNG calls:

  ```rust
  #[cfg(kani)]
  fn mock_random<T: kani::Arbitrary>() -> T { kani::any() }

  #[kani::proof]
  #[kani::stub(rand::random, mock_random)]
  fn verify_with_random() { let _: u32 = rand::random(); }
  ```

  Run with `cargo kani -Z stubbing`. Leave a FIXME with the upstream link
  when a stub works around a tool bug.

## References

- [Kani Rust Verifier](https://github.com/model-checking/kani) and
  [documentation](https://model-checking.github.io/kani/).
- [Tutorial: First Steps](https://model-checking.github.io/kani/tutorial-first-steps.html),
  [Attributes Reference](https://model-checking.github.io/kani/reference/attributes.html),
  [Stubbing](https://model-checking.github.io/kani/reference/experimental/stubbing.html),
  [Function Contracts](https://model-checking.github.io/kani/reference/experimental/contracts.html),
  [Rust Feature Support](https://model-checking.github.io/kani/rust-feature-support.html).
- [`references/project-on-ramp.md`](references/project-on-ramp.md) for
  pins, Makefile targets, CI jobs, contract tests, and documentation.
- [`references/review-failure-modes.md`](references/review-failure-modes.md)
  for the pre-submission checklist drawn from estate review history.
- [`references/harness-examples.md`](references/harness-examples.md) for
  worked harnesses with helpers.
- [`references/kani-harness-example.rs`](references/kani-harness-example.rs)
  for a self-contained Rust source illustrating the four-phase shape.
- The survey behind this guidance:
  `docs/verification-review-failure-modes.md` in the catalogue repository.
