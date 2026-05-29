# Installation note: proptest and friends

Proptest is a regular Cargo crate. There is no separate runner or
toolchain to install — `cargo test` is the driver. This note records
the dependency choices a typical Rust project will need to make once
and the environment variables that gate behaviour at run time.

## Crates and what they are for

```toml
[dev-dependencies]
proptest = "1"
# Optional: derive the default strategy on user types.
proptest-derive = "0.5"
# Optional: alternative derive plus a #[proptest] attribute that
# allows field-dependent strategies.
test-strategy = "0.4"
# Optional: state-machine tests built on top of proptest.
proptest-state-machine = "0.4"
```

- **`proptest`** is the core crate: the `Strategy` trait, the
  `proptest!` and `prop_compose!` macros, the `prop_assert*` family,
  and the `TestRunner` that drives generation, shrinking, and
  failure persistence.
- **`proptest-derive`** is the official `#[derive(Arbitrary)]` macro.
  It works for most enums and structs whose fields can be generated
  with `any::<T>()` and supports a `#[proptest(strategy = "...")]`
  field attribute. The maintainers describe it as somewhat
  experimental; expect occasional breaking changes between
  point releases.
- **`test-strategy`** is a third-party alternative with two extra
  capabilities worth caring about: the `#[strategy(...)]` field
  attribute can reference earlier fields with `#field`
  (for example `#[strategy(0..=#n)]`), and the `#[proptest]`
  attribute on a test function preserves normal `rustfmt` formatting
  rather than wrapping the test body in a macro. Reach for it when
  the default `proptest-derive` cannot express a field-dependent
  strategy without going through a manual `prop_compose!` block.
- **`proptest-state-machine`** layers `ReferenceStateMachine` and
  `StateMachineTest` on top of `proptest`. Use it when a property
  needs a sequence of operations rather than a single input.

Stick with `proptest` plus one of the derive crates by default. Add
`proptest-state-machine` when a property crosses the
single-call/sequence-of-calls boundary.

## Feature flags worth knowing

The `proptest` crate ships several optional features. The defaults
work for ordinary `std`-targeted code; pick the rest deliberately.

- `std` (default) — pulls in `std`-only helpers and enables
  file-based failure persistence. Disable for `no_std` testing.
- `fork` — enables the `fork` field on `ProptestConfig`, which runs
  each case in a subprocess so process-killing failures (stack
  overflow, abort, FFI segfault) can still be reported and shrunk.
  Depends on the `rusty-fork` crate.
- `timeout` — enables the `timeout` field, which kills any case that
  runs longer than _N_ milliseconds. Implies `fork`. Use it when the
  property under test can hang on hostile input.
- `attr-macro` — exposes a `#[proptest]` attribute macro that can
  decorate a `#[test]` function directly, sparing you the `proptest!
  { ... }` outer block. Useful when nested macros confuse other tools
  in your toolchain.
- `default-config-override`, `boxed-union`, `bit-set`, `regex-support`
  — niche features documented in the crate's `Cargo.toml`. Default
  configurations cover most projects.

Pick a small set explicitly so a transitive activation does not
surprise CI:

```toml
proptest = { version = "1", default-features = false, features = [
    "std",
    "fork",
    "timeout",
] }
```

## Environment variables

Proptest reads several environment variables at run time so CI tiers
do not require code changes:

- `PROPTEST_CASES` — successful cases required to pass (default 256).
  Raise it for nightly runs; do not lower it to hide a flake.
- `PROPTEST_FORK` — set to `true` to force every test in the suite to
  fork its cases.
- `PROPTEST_TIMEOUT` — milliseconds per case; implies forking.
- `PROPTEST_MAX_SHRINK_ITERS` — cap on shrink iterations; `0`
  disables shrinking (useful when iterating on a strategy itself).
- `PROPTEST_MAX_LOCAL_REJECTS`, `PROPTEST_MAX_GLOBAL_REJECTS` —
  rejection budgets for `prop_filter` and `prop_assume!`. Treat a
  bumped budget as a signal that the strategy needs reshaping.

Pair a fast everyday run with a slow nightly sweep:

```bash
# Inner loop: default 256 cases.
cargo test --workspace

# Nightly: widen the search and force forks so a pathological case
# cannot abort the whole run.
PROPTEST_CASES=10000 PROPTEST_FORK=true cargo test --workspace
```

Wrap each command in a `Makefile` target (or its equivalent) so CI
and contributors run the same thing.

## What is not in scope here

This note does not install the property-testing tooling beyond the
`Cargo.toml` snippet above. There is no `prover-tools` equivalent for
proptest because there is nothing to install outside Cargo. For tool
selection between proptest and other adversaries, load
[`../rust-verification/SKILL.md`](../../rust-verification/SKILL.md).
