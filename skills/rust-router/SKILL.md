---
name: rust-router
description: Route Rust work to the smallest useful skill. Use for Rust coding, design, compile errors, API questions, crate layout, async, performance, unsafe, or domain-specific Rust work.
metadata:
  globs: "**/Cargo.toml, **/*.rs"
---

# Rust Router

Load this first for non-trivial Rust work, then load only the smallest useful
follow-on skill.

## Working stance

- Start from the concrete problem: error, boundary, hot path, or unsafe edge.
- Prefer one language skill plus at most one domain or architecture skill.
- Use the general `leta` skill for code navigation, references,
  implementations, and refactors.
- If the answer starts turning into a tutorial, stop and cut back to the
  decision that matters.
- When a local fix needs clones, locks, trait-object escape hatches, or unsafe
  code, re-check the design before keeping the patch.

## Route by question

- Polonius adoption, NLL workarounds, defensive clones caused by the borrow
  checker, or borrow-centric API evolution: `nll-to-polonius`
- Ownership, borrowing, aliasing, or interior mutability:
  `rust-memory-and-state`
- Trait bounds, generics, API shape, newtypes, or typestate:
  `rust-types-and-apis`
- Error shape, panic boundary, or library-versus-binary handling:
  `rust-errors`
- Unit-test helper shape, fixtures, table tests, serialized tests, or rich
  assertions: `rust-unit-testing`
- `dead_code`, `unused_imports`, conditional compilation, or deciding whether
  an apparently unused item should be removed: `rust-unused-code`
- Tasks, `Send`/`Sync`, blocking, channels, or cancellation:
  `rust-async-and-concurrency`
- Allocation pressure, layout, or benchmark discipline:
  `rust-performance-and-layout`
- `unsafe`, foreign function interface (FFI), layout guarantees, or soundness:
  `rust-unsafe-and-ffi`
- Crate boundaries, features, public surface, or layering:
  `arch-crate-design`
- Dependency hygiene, `cargo-vet`, `cargo-deny`, SemVer guardrails:
  `arch-supply-chain`
- Recording a hard-to-reverse architectural decision (Y-Statement):
  `arch-decision-records`
- Verification tool selection (Miri, proptest, `cargo-mutants`, `loom`,
  `shuttle`, `turmoil`, Kani, Verus): `rust-verification`; deep dives
  in `proptest`, `kani`, and `verus`
- HTTP services, middleware, or request state: `domain-web-services`
- CLIs, workers, daemons, or long-running jobs: `domain-cli-and-daemons`
- `no_std`, firmware, devices, or edge nodes: `domain-embedded-and-iot`


## Testing hierarchy

This is a decision hierarchy, not a prestige ranking. Pick the first rung
whose evidence matches the question, and stop there.

1. **Named unit test**: choose `rust-unit-testing` when one scenario,
   boundary, regression, rendered output, or error contract matters. The
   test name should explain why that example belongs in the specification.
2. **Parameterized `rstest` table**: choose `rust-unit-testing` when the
   cases form a finite truth table or standards corpus and each row has
   distinct semantic meaning. A table removes duplicated bodies; it should
   not impersonate coverage of an open-ended domain.
3. **Lightweight property test**: choose `proptest` when the same
   invariant, round trip, oracle, or metamorphic relation should hold for
   many cheap, repeatable inputs. A growing list of representative
   `#[case]` rows is the usual signal, and reviewers flag it as "only N
   hardcoded test cases". Start with ranges, regex literals, and
   `any::<T>()`.
4. **Structured or stateful property test**: stay with `proptest` when
   valid values have dependent fields, recursive structure, or bugs depend
   on a sequence of operations. `prop_compose!`, derive crates, and
   `proptest-state-machine` are justified here, not before.
5. **Bounded exhaustive exploration**: choose `kani` when a small pure
   function, dispatch selector, or `unsafe` block carries an invariant and
   every reachable path within a stated bound matters more than sampled
   confidence.
6. **Unbounded proof**: choose `verus` when the property must hold for
   any length or ordering and a small, stable pure kernel exists to prove
   it over.

`cargo-mutants` sits beside the hierarchy rather than above it. Choose it
when the behaviour is already specified and the question is whether the
suite would notice a plausible defect. Miri sits below it: run it on the
tests that already exist whenever they touch `unsafe`.

Leave this hierarchy when the failure depends primarily on a schedule,
a real service, load, memory use, or a foreign boundary. Use `loom`,
`shuttle`, or `turmoil`, integration tests, benchmarks and profilers, or
sanitizers instead.


## Testing selection rubric

Ask these questions in order:

- Is this one meaningful scenario or a finite set of normative cases? Use
  a named test or an `rstest` table.
- Should one semantic relation hold over a broad, cheap input space? Use a
  lightweight `proptest` property.
- Does generating valid input require a domain model, or does operation
  history matter? Escalate within `proptest`.
- Must every reachable path through a small bounded function satisfy an
  invariant? Use `kani`.
- Must the property hold without a bound? Extract the pure kernel and use
  `verus`.
- Do the tests pass, but their ability to detect wrong code remains
  unclear? Use `cargo-mutants`.
- Does the failure depend on scheduling, external state, or performance?
  Leave the property and proof tools for a specialist test.

Examples remain valuable at every rung. Keep exact protocol examples and
named regressions beside a property; do not delete readable specification
merely because a generator can rediscover it.

## Pairing rules

- A clear lightweight invariant goes straight to `proptest`; no selector
  ceremony is required.
- Load `rust-verification` when the testing rung or escalation path is
  unclear, then choose one primary adversary. `cargo-mutants` may pair
  with any rung because it audits the suite rather than generating
  production inputs.
- Polonius migrations usually pair `nll-to-polonius` with
  `rust-types-and-apis` only when public API compatibility constrains the
  migration.
- Web services usually pair `domain-web-services` with
  `rust-async-and-concurrency` or `rust-errors`.
- CLIs and daemons usually pair `domain-cli-and-daemons` with `rust-errors`.
- Embedded and IoT usually pair `domain-embedded-and-iot` with
  `rust-memory-and-state` or `rust-unsafe-and-ffi`.
- If two language skills both seem necessary, load the one that explains the
  failure and keep the other in reserve.

## Escalate when

- borrow-checker fixes keep adding clones or `Arc<Mutex<_>>` without clarity,
- a public API needs `dyn Any`, erased errors, or unstable generic sprawl,
- async code requires shared mutable state and cancellation semantics at once,
- performance claims appear before measurements,
- unsafe code exists without a crisp invariant list,
- a lightweight property needs heavy rejection, recursive generation, or
  an operation model to reach valid cases,
- a critical pure function needs exhaustive path scrutiny rather than
  sampled confidence,
- a passing suite gives no evidence that its assertions detect wrong
  behaviour.

Read [routing-matrix.md](references/routing-matrix.md) only when the route is
still unclear.
