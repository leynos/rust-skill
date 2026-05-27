# Changelog

All notable changes to this project are recorded in this file.

The format is based on [Common Changelog](https://common-changelog.org).

## [Unreleased]

### Added

- `rust-verification` skill: routes Rust verification work to the
  smallest adversary that matches the failure mode (Miri, sanitizers,
  proptest, cargo-mutants, turmoil, loom, shuttle, Kani, Verus). Ships
  with two references: per-tool rationale and the determinism fences
  that chaos tools require.
- `arch-supply-chain` skill: frames the dependency graph as a
  deliberately shaped trust surface. Covers cargo-audit, cargo-deny,
  cargo-vet, cargo-semver-checks, cargo-public-api, lockfile policy,
  and MSRV pinning. References cover the cargo-vet trust model and
  day-to-day dependency hygiene patterns.
- `arch-decision-records` skill: captures architectural decisions in
  Y-Statement form, with three Rust-flavoured worked examples
  (typestate, verification-tool selection, unsafe alignment invariant).
- `kani` skill: imported from `agent-helper-scripts` and rewired to
  install via `rust-prover-tools`. Replaces HNSW-specific examples with
  neutral graph-with-bidirectional-links harnesses; ships harness
  examples and a reference Rust source.
- `verus` skill: imported from `agent-helper-scripts` and rewired to
  install and run via `rust-prover-tools`. Replaces HNSW-specific
  examples with neutral `EdgeSpec`/`ItemSpec` proofs; ships worked
  proof examples, a reference Rust source, and an installation note.
- `rust-memory-and-state/references/encapsulation-and-raii.md`:
  ownership as architectural decoupling, RAII via `Drop`, and
  `Mutex`/`MutexGuard` as the canonical wireframe.
- `rust-unsafe-and-ffi/references/unsafecell-and-interior-mutability.md`:
  why `UnsafeCell` is the only sound foundation for shared mutation,
  the invariants wrappers must enforce, and common UB pitfalls.
- `rust-types-and-apis/references/misuse-resistant-apis.md`: typestate,
  newtype with hidden inner, anti-boolean-blindness with domain enums,
  API Guidelines checklist, and SemVer tooling.
- `rust-performance-and-layout/references/rigorous-benchmarking.md`:
  Tango paired benchmarking, iai-callgrind, open- versus closed-loop
  load models, tail-latency CDFs, and goodput.

### Changed

- `rust-unsafe-and-ffi/SKILL.md`: added the missing-`UnsafeCell` red
  flag, a reference to the new interior-mutability material, and a
  cross-link to the `rust-verification` skill.
- `rust-types-and-apis/SKILL.md`: added the boolean-blindness red flag
  and a reference to the new misuse-resistant-APIs material.
- `rust-memory-and-state/SKILL.md`: added the encapsulation-and-RAII
  reference link.
- `rust-performance-and-layout/SKILL.md` and `benchmark-discipline.md`:
  added pointers to the new rigorous-benchmarking reference.
- `arch-crate-design/SKILL.md`: cross-linked the new `arch-supply-chain`
  skill from the packaging guidance.

### Documentation

- `docs/execplans/advanced-encapsulation-and-verification.md`: the
  living ExecPlan governing this changelog block. Progress, surprises,
  and decisions are recorded inline as work advances.
- `docs/users-guide.md`: operator-facing guide covering catalogue
  installation, router invocation, and when to reach for the new
  verification, supply-chain, and decision-record skills. Linked from
  the README.
