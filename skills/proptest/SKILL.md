---
name: proptest
description: Write and maintain proptest property tests for Rust, including custom strategies, shrinking discipline, regression files, and state-machine tests. Use when checking that a property holds across a generated input domain and when a unit test or example does not exercise enough of the input space.
---

# Proptest property-based testing for Rust

Proptest generates many random inputs against a property, then shrinks
any failing case to a minimal counter-example. It is the cheapest
verification adversary for pure functions whose input domain is too
large to enumerate. Load the `rust-verification` skill first for the
selection rules; load this skill once proptest is the chosen tool.

## When to apply

Apply when a pure function has an algebraic property (round-trip,
idempotence, ordering, conservation, monotonicity,
length-preservation), when a parser or codec must round-trip across
all valid inputs, when an oracle is available (reference
implementation, invariant predicate, prior version), or when a
unit-test corpus keeps growing because each new bug needs another
hand-written case.

Do not apply when the property requires exhaustive coverage of a
bounded space (use Kani), when it must hold for unbounded inputs with
a proof (use Verus), when the bug is a scheduling artefact (use
`loom`, `shuttle`, or `turmoil`), or when the failure mode is
undefined behaviour in `unsafe` code (use Miri first).

## Installation

Proptest is a regular crate; no separate tool is needed.

```toml
[dev-dependencies]
proptest = "1"
# Optional: derive Arbitrary on user types.
proptest-derive = "0.5"
# Optional: alternative derive with higher-order strategies.
test-strategy = "0.4"
```

Tests run under the normal `cargo test` driver. The environment
variables `PROPTEST_CASES`, `PROPTEST_FORK`, `PROPTEST_TIMEOUT`, and
`PROPTEST_MAX_SHRINK_ITERS` override per-test configuration without
recompiling. See
[`references/installation-note.md`](references/installation-note.md)
for the derive-crate comparison and the feature-flag matrix.

## Core concepts

A property test pairs a **strategy** (how to generate values) with a
property assertion. The `proptest!` macro wires both into a `#[test]`
function:

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn parse_roundtrips(y in 0u32..10_000, m in 1u32..=12, d in 1u32..=28) {
        let s = format!("{y:04}-{m:02}-{d:02}");
        let parsed = parse_date(&s).expect("valid date should parse");
        prop_assert_eq!(parsed, (y, m, d));
    }
}
```

Key pieces:

- A **strategy** is anything implementing `Strategy<Value = T>`.
  Ranges (`0u32..10_000`), regex literals (`"[a-z]+"`), and
  `any::<T>()` are the everyday starting points.
- `prop_assert!`, `prop_assert_eq!`, and `prop_assert_ne!` report
  failure to the runner instead of panicking; this preserves
  shrinking.
- `prop_assume!(cond)` rejects the current case as not interesting.
  Use it only for cheap rare-edge filtering; for anything common,
  construct valid inputs by composition.
- `prop_compose!` builds reusable strategies returning structured
  values: first list is public parameters, second draws from inner
  strategies, body returns the value.
- Custom types derive a default strategy via
  `#[derive(proptest_derive::Arbitrary)]` or, with better ergonomics
  and field-dependent strategies, via `test-strategy`.

A worked round-trip example with `prop_compose!`, a state-machine
sketch with `proptest-state-machine`, and the field-dependent
`#[strategy(0..=#n)]` pattern from `test-strategy` live in
[`references/strategy-examples.md`](references/strategy-examples.md).
A self-contained Rust source is in
[`references/proptest-example.rs`](references/proptest-example.rs).

## The filtering trap

Filtering invalid inputs out is almost always the wrong shape. Both
`prop_filter` and `prop_assume!` use rejection sampling, and the
runner will abort once the rejection budget is exhausted. Worse,
shrinking and filtering interact badly: when a shrunk candidate is
rejected, the runner cannot tell whether the shrink should continue,
so it backs off and the minimised counter-example is larger than it
needs to be.

The fix is to construct only valid values from the seed. Replace a
`prop_filter` that keeps even numbers with a strategy that draws half
the range and doubles it; replace a `prop_assume!` that demands
`a < b` with a strategy that draws `b` then draws `a` from `0..b`.
`prop_assume!` is acceptable only when the rejected case is genuinely
rare; it is wrong when the rejection is structural. Before-and-after
worked examples live in
[`references/strategy-examples.md`](references/strategy-examples.md).

## Anti-patterns

- **`panic!`, `assert!`, or `unwrap` inside the body.** Use
  `prop_assert*` so the runner can shrink. A `.unwrap()` on a
  generated value should be replaced by a strategy that excludes the
  `None`/`Err` case at the source.
- **Asserting "doesn't panic".** This catches only the most obvious
  bugs and tells you nothing about correctness. Pair it with a real
  property (round-trip, oracle comparison, invariant).
- **Re-implementing the function under test.** If the property says
  "the result equals `f_again(input)`" where `f_again` is the same
  algorithm, the test proves only that the developer can copy code.
  Use a structurally different oracle (reference implementation,
  slow brute force, prior version).
- **Hiding regressions.** A `proptest-regressions/` file with a
  failing seed must be promoted to a named unit test with the shrunk
  input pinned and a comment recording the bug.
- **Tuning `cases` to make a flake go away.** If the property fails
  on case 500 but not on case 256, the test has found a bug.
  Investigate; do not lower the case count.

## What proptest detects and what it does not

Detects: violated algebraic properties on generated inputs, panics on
inputs the strategy can reach, round-trip mismatches, oracle
divergence, and (with `fork`+`timeout`) stack overflows and hangs.

Does not detect: undefined behaviour the property does not name (use
Miri or sanitizers), bugs that need a specific schedule (use `loom`,
`shuttle`, or `turmoil`), invariants the strategy cannot reach because
it never generates the triggering shape, and anything outside the
input space the strategies describe. A passing proptest is strong
evidence, not a proof.

## Project integration

- **Check `proptest-regressions/` into version control** so CI replays
  failing seeds before generating new cases.
- **Promote shrunk failures to named unit tests** — the regression
  file is a backstop, not the system of record.
- **Tier the runs.** Keep the default `cases = 256` for `cargo test`,
  then run a nightly job with `PROPTEST_CASES=10000` to widen the
  search without slowing the inner loop.
- **Validate every property with a deliberate mutation.** Break the
  production code, confirm the property fails with a useful shrunk
  input, then restore. `cargo-mutants` automates this across the
  suite.

## Configuration knobs

The everyday knobs on `ProptestConfig` worth knowing inline:

- `cases` (default 256) — successful cases required to pass.
- `max_shrink_iters` (default `4 * cases`) — cap on shrink steps;
  `0` disables shrinking while investigating.
- `fork` (off; needs the `fork` feature) — run each case in a
  subprocess so stack overflows and aborts can still be shrunk.
- `timeout` (off; implies `fork`; needs the `timeout` feature) —
  kill a case after _N_ milliseconds.
- `failure_persistence` — defaults to
  `FileFailurePersistence::SourceParallel("proptest-regressions")`.

Configure inside the macro with
`#![proptest_config(ProptestConfig { cases: 1024, .. ProptestConfig::default() })]`.

## State-machine tests

For stateful systems, `proptest-state-machine` generates sequences
of transitions and shrinks failing sequences. Implement
`ReferenceStateMachine` for the abstract model and `StateMachineTest`
for the system under test; the runner drives both, checks invariants
after each step, and shrinks to the smallest failing trace. The
pattern shines on collections, caches, allocators, and protocol
clients where the bug needs a particular history to surface. See
the counter-and-system worked example in
[`references/strategy-examples.md`](references/strategy-examples.md).

## Hard-won lessons

- **Strategies decide what you test.** A weak strategy makes a
  strong property look strong. Audit the strategy first.
- **Shrinking is sacred.** Never panic or `unwrap` inside the body;
  never tune `cases` to hide a failure; never filter when you can
  compose.
- **Regression files are not regression tests.** Promote each
  failure to a named unit test with the shrunk input pinned.
- **Derives have edges.** `proptest-derive` is fine for most enums
  and structs; `test-strategy` handles recursive types and
  field-dependent strategies at the cost of an extra dependency.
- **Pair with `cargo-mutants`.** Proptest shows the property holds
  for the inputs the strategy reaches; mutation testing shows the
  property would notice if the production code were wrong. Both are
  needed.

## References

- [Proptest book](https://proptest-rs.github.io/proptest/) and
  [GitHub repository](https://github.com/proptest-rs/proptest).
- [Strategy trait](https://docs.rs/proptest/latest/proptest/strategy/trait.Strategy.html),
  [`prop_compose!` tutorial](https://proptest-rs.github.io/proptest/proptest/tutorial/macro-prop-compose.html),
  [Filtering pitfalls](https://altsysrq.github.io/proptest-book/proptest/tutorial/filtering.html),
  [Failure persistence](https://altsysrq.github.io/proptest-book/proptest/failure-persistence.html),
  [Forking and timeouts](https://altsysrq.github.io/proptest-book/proptest/forking.html),
  [State-machine testing](https://proptest-rs.github.io/proptest/proptest/state-machine.html).
- [`proptest-derive`](https://docs.rs/proptest-derive) and
  [`test-strategy`](https://docs.rs/test-strategy).
- [`references/strategy-examples.md`](references/strategy-examples.md)
  for worked strategy patterns, the filtering-trap fix, and the
  state-machine sketch.
- [`references/proptest-example.rs`](references/proptest-example.rs)
  for a self-contained Rust source.
- Selection between proptest and other verification tools lives in
  [`../rust-verification/SKILL.md`](../rust-verification/SKILL.md).
