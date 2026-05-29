---
name: arch-supply-chain
description: Audit and curate a Rust project's dependency graph. Use for `cargo-vet`, `cargo-audit`, `cargo-deny`, lockfile hygiene, version pinning, and the policy of who is trusted to ship what. Also for SemVer guardrails (`cargo-semver-checks`, `cargo-public-api`) at the publishing boundary.
---

# Rust supply-chain hygiene

A Rust project's attack surface is the union of every crate in its
dependency graph, recursively. Shape, audit, and shrink the graph
deliberately; do not let it grow as a side effect of `cargo add`.

## Working stance

- Every transitive dependency is a trust decision; make it explicit
  before the binary ships.
- Prefer fewer, better-known dependencies over many small ones.
- The lockfile is policy. Review `Cargo.lock` diffs like source diffs.
- Audit continuously, not just at release time.

## Decision surface

| Question                                             | Tool                  |
| ---------------------------------------------------- | --------------------- |
| Any dependencies in the RustSec advisory DB?         | `cargo-audit`         |
| Any dependencies violating project policy?           | `cargo-deny`          |
| Has this crate been reviewed by someone I trust?     | `cargo-vet`           |
| Does this PR break my public API?                    | `cargo-semver-checks` |
| What is the precise public surface of this crate?    | `cargo-public-api`    |

`cargo-vet` is the decentralised audit format. Imports from peer
projects (Mozilla, Google, Bytecode Alliance) widen the trusted set
without forcing each team to audit everything from scratch.
[`references/cargo-vet-and-trust.md`](references/cargo-vet-and-trust.md)
expands on the trust model.

## Lockfile policy

- Commit `Cargo.lock` for every binary; commit it for libraries unless
  the publishing workflow needs resolver freedom.
- Pin the MSRV in `Cargo.toml` and verify it in CI on the oldest
  supported toolchain.
- Renovate or Dependabot must propose lockfile changes via PR; never
  rewrite the lockfile in-place on `main`.

## SemVer at the publishing boundary

Public crates owe their callers stability. Two tools make breakage
visible before publication:

- **`cargo-semver-checks`** compares the working tree against the most
  recently published version and reports breaking changes at the type
  and trait level.
- **`cargo-public-api`** prints the full public surface so reviewers
  can see the diff. Commit a snapshot file; fail CI when the snapshot
  changes without a corresponding version bump.

Use both: `cargo-semver-checks` catches the violations it knows about;
`cargo-public-api` catches the rest.

## Dependency hygiene patterns

See [`references/dependency-hygiene.md`](references/dependency-hygiene.md)
for worked patterns:

- shrinking the graph (default-features off, single-feature crates),
- detecting duplication (`cargo tree -d`),
- isolating riskier crates behind feature flags,
- recording deny/allow policy in-tree (`deny.toml`, `supply-chain/`).

## Red flags

- New dependencies arrive without a vet entry, audit advisory check, or
  reviewer comment justifying the addition.
- `Cargo.lock` diffs are dismissed as "just dependency updates" without
  a reviewer reading them.
- A crate is added for a single helper function that could be inlined
  in tens of lines.
- A public crate publishes a major or minor version bump without
  running `cargo-semver-checks` and `cargo-public-api`.
- The MSRV in `Cargo.toml` drifts ahead of the documented MSRV without
  a version bump.
- `cargo-vet` exemptions accumulate and are never converted to audits.

## Cross-references

- Crate boundaries and feature design: see
  [`arch-crate-design`](../arch-crate-design/SKILL.md).
- Trust-model background: see
  [`references/cargo-vet-and-trust.md`](references/cargo-vet-and-trust.md).
- Day-to-day hygiene: see
  [`references/dependency-hygiene.md`](references/dependency-hygiene.md).
