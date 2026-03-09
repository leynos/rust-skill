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

## Route by question

- Ownership, borrowing, aliasing, or interior mutability:
  `rust-memory-and-state`
- Trait bounds, generics, API shape, newtypes, or typestate:
  `rust-types-and-apis`
- Error shape, panic boundary, or library-versus-binary handling:
  `rust-errors`
- Tasks, `Send`/`Sync`, blocking, channels, or cancellation:
  `rust-async-and-concurrency`
- Allocation pressure, layout, or benchmark discipline:
  `rust-performance-and-layout`
- `unsafe`, FFI, layout guarantees, or soundness:
  `rust-unsafe-and-ffi`
- Crate boundaries, features, public surface, or layering:
  `arch-crate-design`
- HTTP services, middleware, or request state: `domain-web-services`
- CLIs, workers, daemons, or long-running jobs: `domain-cli-and-daemons`
- `no_std`, firmware, devices, or edge nodes: `domain-embedded-and-iot`

## Pairing rules

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
- async code needs shared mutable state and cancellation semantics at once,
- performance claims appear before measurements,
- unsafe code exists without a crisp invariant list.

Read [routing-matrix.md](references/routing-matrix.md) only when the route is
still unclear.
