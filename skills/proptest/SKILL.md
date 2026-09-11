---
name: proptest
description: Write and maintain proptest property tests for Rust, including custom strategies, shrinking discipline, regression files, and state-machine tests. Use when checking that a property holds across a generated input domain, when a unit test or example does not exercise enough of the input space, and when a reviewer or pre-merge check asks whether a change needs a property test.
---

# Proptest property-based testing for Rust

Proptest generates many random inputs against a property, then shrinks
any failing case to a minimal counter-example. It is the cheapest
verification adversary for pure functions whose input domain is too
large to enumerate. Load the `rust-verification` skill first for the
selection rules; load this skill once proptest is the chosen tool.

## Is a property test expected?

Reviewers and pre-merge checks apply one rule: a property test (or a
bounded model checker) is expected whenever a change introduces an
invariant over a range of inputs, states, orderings, or transitions.
Parsers, canonicalizers, normalizers, merge and precedence rules,
bounded queues, and validators over a range all qualify; two to four
example cases do not discharge them. The check fires as a warning,
repeats every round until satisfied, and treats a PR body that claims
coverage which does not exist as a defect.

The rule cuts both ways. A small, finite space that is enumerated and
run in full on every build (four literals, six permutations) wants
`rstest` cases, not a generator, and an unsolicited property test where
the design decided against one is also flagged. Decide which side the
change falls on and say so: either land the property, defer it to a
tracked issue, or write a one-paragraph scope statement where the
reviewer will look. Silence is the only answer that fails. A template
for the statement is in
[`references/sibling-module-template.md`](references/sibling-module-template.md).

## When to apply

Apply when a pure function has an algebraic property (round-trip,
idempotence, ordering, conservation, monotonicity,
length-preservation), when a parser or codec must round-trip across
all valid inputs, when an oracle is available (reference
implementation, invariant predicate, prior version), or when a
unit-test corpus keeps growing because each new bug needs another
hand-written case.

Treat a lightweight property as ordinary testing when the code is cheap
to run, repeatable, and governed by a clear invariant. Start with a
range or `any::<T>()`, one semantic assertion, and default settings.
Custom strategies, configuration, and state machines are escalation
tools, not an entrance fee.

## Start light

An `rstest` table often samples a property without saying so:

```rust
#[rstest]
#[case(0)]
#[case(1)]
#[case(127)]
#[case(128)]
#[case(u64::MAX)]
fn varint_roundtrips(#[case] n: u64) {
    assert_eq!(decode_varint(&encode_varint(n)), n);
}
```

Replace the representative sample with the domain, and keep any named
edge case as an explicit unit test beside it:

```rust
proptest! {
    #[test]
    fn varint_roundtrips(n in any::<u64>()) {
        prop_assert_eq!(decode_varint(&encode_varint(n)), n);
    }
}

#[test]
fn varint_roundtrips_at_the_one_byte_boundary() {
    assert_eq!(decode_varint(&encode_varint(128)), 128);
}
```

That is a complete property test. Do not add `prop_compose!`,
`prop_assume!`, a `ProptestConfig`, or a state machine unless the domain
forces the issue.

A `#[case]` table is probably trying to do property testing when every
row exercises the same assertion relation, the values are described as
representative or edge cases, another bug adds another row without
changing the test's meaning, several columns manually sample a
cross-product, or the expected value comes from a simple invariant or a
structurally different reference. Keep the table when the rows form a
finite truth table or protocol corpus, each row has distinct semantic
meaning, exact rendered output or error text matters, or the test is too
slow or impure to repeat freely. A four-row standards table does not
need a generator orbiting it.

## Everyday properties

Prefer properties that state behaviour independently of the
implementation:

- **Round trip:** `decode(encode(x)) == x`.
- **Idempotence:** `normalize(normalize(x)) == normalize(x)`.
- **Oracle or differential:** the optimized path agrees with a slow,
  obviously different reference.
- **Invariant or conservation:** sorting preserves the multiset; a
  transaction preserves total value; a transform preserves a schema.
- **Metamorphic relation:** changing the input in a known way changes,
  or does not change, the output predictably.
- **Totality or robustness:** valid-shaped input does not panic. Use this
  only when accepting all such input is itself the contract; otherwise
  assert a stronger semantic fact too.

## Escalation ladder

Stop at the first rung that answers the question:

1. **Lightweight property:** ranges, regex literals, `any::<T>()`, one
   invariant, default settings. This should be the common case.
2. **Structured values:** `prop_compose!` or a derive crate when the
   input is a struct or enum.
3. **Dependent or recursive values:** `prop_flat_map`, `test-strategy`
   field references, or recursive strategies only when valid fields
   depend on one another or the data is recursive.
4. **Operation histories:** `proptest-state-machine` when bugs depend on
   sequences such as insert, delete, reorder, cache invalidation, or
   protocol transitions.
5. **Bounded path scrutiny:** move to `kani` when a small pure function
   carries an invariant and every reachable path within a bound matters
   more than broad sampling.
6. **Suite sensitivity:** add `cargo-mutants` when the question is
   whether the tests would notice a defect. Mutation testing audits the
   suite; it does not replace the property.

Escalate from a light property when the strategy starts encoding
substantial domain rules, rejection dominates generation, the failure
depends on history, or the assurance target changes from broad search to
bounded exploration, unbounded proof, or suite sensitivity. Load
`rust-verification` when that choice is unclear.

Do not apply when the property requires exhaustive coverage of a
bounded space (use Kani), when it must hold for unbounded inputs with
a proof (use Verus), when the bug is a scheduling artefact (use
`loom`, `shuttle`, or `turmoil`), or when the failure mode is
undefined behaviour in `unsafe` code (use Miri first).

## Installation

Proptest is a regular crate; no separate tool is needed.

```toml
[workspace.dependencies]
proptest = "1.11" # minimum compatible minor; use "=x.y.z" for an exact pin

[dev-dependencies]
proptest = { workspace = true }
# Optional: derive Arbitrary on user types.
proptest-derive = "0.5"
# Optional: alternative derive with higher-order strategies.
test-strategy = "0.4"
# Optional: stateful tests built on top of proptest.
proptest-state-machine = "0.4"
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
- Each function inside `proptest!` needs its own `#[test]`; without it
  the block compiles, generates nothing, and passes.
- `prop_assert!`, `prop_assert_eq!`, and `prop_assert_ne!` report
  failure to the runner instead of panicking; this preserves
  shrinking.
- `prop_assume!(cond)` rejects the current case as not interesting.
  Use it only for cheap rare-edge filtering, only as a precondition
  before the call under test, and never on the output; for anything
  common, construct valid inputs by composition.
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

## Audit the strategy before the assertion

The most frequent quality finding is a generator that cannot reach the
shape the property claims to test. Before writing assertions, list the
documented input variants and state transitions and check that the
strategy produces each one:

- every generated binding must influence an assertion;
- bounds must be able to hit the limits under test (a queue-limit
  property needs inputs that exceed the limit);
- one generator per documented variant (quoted and unquoted forms,
  escapes, indentation levels, each enum arm derived from the canonical
  `ALL` constant, the full grammar rather than its common subset);
- the strategy must not emit impossible input: transform the generator
  (exclude the delimiter, prefix the segment) rather than filtering;
- ranges must match the documented bounds exactly;
- both branches of any conditional assertion must be constrained.

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
rare; it is wrong when the rejection is structural, when it excludes a
case the code must handle, or when it gates on the environment (check
that once, outside the block). Before-and-after worked examples live in
[`references/strategy-examples.md`](references/strategy-examples.md).

## Anti-patterns

- **`panic!`, `assert!`, or `unwrap` inside the body.** Use
  `prop_assert*` so the runner can shrink. A `.unwrap()` on a
  generated value should become either a strategy that excludes the
  `None`/`Err` case, when the property's precondition genuinely
  requires success, or a `prop_assert!(matches!(..))` on the expected
  variant; documented `None` and `Err` inputs are part of the domain
  and must stay reachable. Whether `.expect("context")` is
  preferred or denied inside test bodies is a per-repository lint
  policy; read the workspace `[lints]` table first, and route fallible
  setup helpers through `TestCaseError`.
- **Asserting "doesn't panic".** This catches only the most obvious
  bugs and tells you nothing about correctness. Pair it with a real
  property (round-trip, oracle comparison, invariant).
- **Re-implementing the function under test.** If the property says
  "the result equals `f_again(input)`" where `f_again` is the same
  algorithm, the test proves only that the developer can copy code.
  Use a structurally different oracle (reference implementation,
  slow brute force, prior version), and keep the oracle's construction
  identical to production down to edge-case clamping.
- **Tautologies.** An assertion the fixture guarantees by construction,
  or one that does not depend on the generated value, is not a
  property. A property derived from current behaviour rather than the
  intended invariant certifies the bug.
- **Disjunctive assertions.** `prop_assert!(a || b)` accepting two
  observed behaviours usually masks a defect.
- **Building a strategy framework before the first property.** Start
  with primitive strategies and let real constraints justify
  abstraction.
- **A state machine for a pure function.** A plain `proptest!` block is
  cheaper to read, run, and debug.
- **Swallowing the assertion.** An early `return Ok(())` on the `Err`
  branch, or a `match` arm that asserts nothing, means the runner sees
  no failure and the bug survives.
- **Hiding regressions.** A `proptest-regressions/` file with a
  failing seed must be promoted to a named unit test with the shrunk
  input pinned and a comment recording the bug.
- **Tuning `cases` to make a flake go away.** If the property fails
  on case 500 but not on case 256, the test has found a bug.
  Investigate; do not lower the case count. `cases: 1` is a signal of
  unresettable global state, not a configuration.

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

- **Start in a sibling module.** Most repositories cap files at 400
  lines and require a `//!` comment on every module; a `prop_tests.rs`
  plus `prop_strategies.rs` pair next to the module avoids a mid-review
  extraction. Follow the repository's convention where it keeps blocks
  inline. The template is in
  [`references/sibling-module-template.md`](references/sibling-module-template.md).
- **Check `proptest-regressions/` into version control** so CI replays
  failing seeds before generating new cases. Persistence is keyed to the
  declaring source file: rename the regression file when the source
  moves, and never `#[path]`-include a property file that Cargo also
  discovers as its own target. Disable persistence during mutation
  runs so injected-defect seeds are neither committed nor ignored.
- **Promote shrunk failures to named unit tests** — the regression
  file is a backstop, not the system of record.
- **Tier the runs.** Keep the default `cases = 256` for `cargo test`,
  then run a nightly job with `PROPTEST_CASES=10000` to widen the
  search without slowing the inner loop. Read the budget from the
  environment through one shared profile helper; `fork` and `cases`
  multiply, and a downstream loader that re-reads `PROPTEST_CASES` can
  silently override a cap.
- **Keep the property deterministic.** `HashMap`'s `RandomState` is
  outside proptest's seed, so shrinking and saved seeds stop
  reproducing; use ordered or seeded maps for anything the property
  observes. Do not describe `ProptestConfig::default()` as
  deterministic. Take the environment lock inside the strategy helper,
  not across an iteration. No wall-clock assertions inside a property.
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
- `rng_seed` — set only when standardizing determinism, and keep
  `PROPTEST_RNG_SEED` overridable.

Configure inside the macro with
`#![proptest_config(ProptestConfig { cases: 1024, .. ProptestConfig::default() })]`.
A documented budget that the block does not set is a review finding.

## State-machine tests

For stateful systems, `proptest-state-machine` generates sequences
of transitions and shrinks failing sequences. Implement
`ReferenceStateMachine` for the abstract model and `StateMachineTest`
for the system under test; the runner drives both, checks invariants
after each step, and shrinks to the smallest failing trace. The
pattern shines on collections, caches, allocators, and protocol
clients where the bug needs a particular history to surface. Make sure
every operation class is actually driven; a stubbed transition that
returns `Ok(false)` silently removes it from the model. See
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
- **Say what you did not test.** A scope statement costs a paragraph;
  a missing-property warning costs a review round.

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
- [`references/review-failure-modes.md`](references/review-failure-modes.md)
  for the pre-submission checklist drawn from estate review history.
- [`references/sibling-module-template.md`](references/sibling-module-template.md)
  for the file layout, a strategies module, and the scope statement.
- [`references/strategy-examples.md`](references/strategy-examples.md)
  for worked strategy patterns, the filtering-trap fix, and the
  state-machine sketch.
- [`references/proptest-example.rs`](references/proptest-example.rs)
  for a self-contained Rust source.
- Selection between proptest and other verification tools lives in
  [`../rust-verification/SKILL.md`](../rust-verification/SKILL.md).
- The survey behind this guidance:
  `docs/verification-review-failure-modes.md` in the catalogue repository.
