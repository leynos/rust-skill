---
name: rust-router
description: Route Rust work to the smallest useful skill. Use for Rust coding, design, compile errors, API questions, crate layout, async, performance, unsafe, or domain-specific Rust work.
globs: ["**/Cargo.toml", "**/*.rs"]
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

## Establish borrow-checker posture

For borrow-sensitive ownership, API, async, or performance work, establish the
project's borrow-checker posture before recommending defensive workarounds.
Classify it as `nll`, `polonius-alpha`, `polonius-legacy`, or `unknown`.

- Inspect `rust-toolchain.toml`, `rust-toolchain`, `.cargo/config.toml`,
  `.cargo/config`, CI commands, and relevant `RUSTFLAGS`.
- An explicit `-Zpolonius=next`, `-Zpolonius=off`, or
  `-Zpolonius=legacy` is decisive.
- Current nightly enables Polonius Alpha by default unless the project opts
  out with `-Zpolonius=off`.
- For dated nightlies, compiler wrappers, or future stable compilers, use the
  compile canary in
  [polonius-alpha.md](references/polonius-alpha.md) instead of guessing from
  the channel name.

Treat posture as ambient context and route the concrete question normally. Do
not load `nll-to-polonius` merely because a project uses Polonius Alpha; load
it when adoption, workaround retirement, or API migration is itself the task.

## Route by question

- Polonius adoption, NLL workaround audits, defensive clones caused by the
  borrow checker, or borrow-centric API evolution: `nll-to-polonius`
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

## Pairing rules

- Polonius migrations usually pair `nll-to-polonius` with
  `rust-types-and-apis` only when public API compatibility constrains the
  migration.
- The shared Polonius posture reference is context, not a second first-class
  skill.
- Web services usually pair `domain-web-services` with
  `rust-async-and-concurrency` or `rust-errors`.
- CLIs and daemons usually pair `domain-cli-and-daemons` with `rust-errors`.
- Embedded and IoT usually pair `domain-embedded-and-iot` with
  `rust-memory-and-state` or `rust-unsafe-and-ffi`.
- If two language skills both seem necessary, load the one that explains the
  failure and keep the other in reserve.

## Escalate when

- borrow-checker fixes keep adding clones or `Arc<Mutex<_>>` without clarity,
- a recommendation depends on borrow acceptance but the project posture is
  still unknown,
- a public API needs `dyn Any`, erased errors, or unstable generic sprawl,
- async code requires shared mutable state and cancellation semantics at once,
- performance claims appear before measurements,
- unsafe code exists without a crisp invariant list.

Read [polonius-alpha.md](references/polonius-alpha.md) when borrow-checker
posture materially changes the design. Read
[routing-matrix.md](references/routing-matrix.md) only when the route is still
unclear.
