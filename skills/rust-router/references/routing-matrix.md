# Routing Matrix

Use this when the first skill is not obvious.

- `E0382`, `E0502`, `E0597`, moved value, or borrow overlap:
  `rust-memory-and-state`, then `rust-types-and-apis` if the local fix still
  looks wrong.
- Trait bound failures, object safety, `impl Trait`, or public API shape:
  `rust-types-and-apis`, then `arch-crate-design` if the boundary is public.
- `Result` shape, `thiserror`, `anyhow`, retryability, or panic policy:
  `rust-errors`, then `arch-crate-design` if crates or binaries disagree.
- `Send`, `Sync`, `spawn`, channel choice, or async shutdown:
  `rust-async-and-concurrency`, then `domain-web-services` when request
  handling or service shutdown is involved.
- Allocation churn, enum size, layout, cache locality, or benchmarks:
  `rust-performance-and-layout`, then `arch-crate-design` if the fix changes
  public shape or layering.
- Raw pointers, `NonNull`, `MaybeUninit`, or `extern "C"`:
  `rust-unsafe-and-ffi` (foreign function interface (FFI)), then
  `domain-embedded-and-iot` (Internet of Things (IoT)) when hardware or edge
  constraints matter.
- A property must be proved rather than tested (UB sweep, schedule
  chaos, structural invariant, algebraic property):
  `rust-verification` to pick the tool, then `kani` for bounded model
  checking or `verus` for deductive proofs.
- Dependency audit, lockfile policy, banned crates, or breaking-change
  detection: `arch-supply-chain`, then `arch-crate-design` if the fix
  touches public surface.
- A decision is hard to reverse (typestate edges, `unsafe` invariants,
  runtime choice, verification-tool choice): `arch-decision-records`
  alongside the language or architecture skill that owns the design.

Domain pairings:

- Web backends: `domain-web-services` plus the language skill that matches the
  concrete failure.
- CLI tools and background jobs: `domain-cli-and-daemons` plus `rust-errors`,
  or `rust-async-and-concurrency` if lifecycle and shutdown matter.
- Embedded and edge-device work: `domain-embedded-and-iot` plus
  `rust-memory-and-state` or `rust-unsafe-and-ffi`.

Avoid loading more than two first-class skills until a real gap appears.
