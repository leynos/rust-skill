# Dependency hygiene patterns

The dependency graph is shaped by every `Cargo.toml` edit. A handful of
repeatable patterns keep the graph small, auditable, and consistent
across CI.

## Shrink the graph

### Default features off

Many widely used crates pull in surprising transitive dependencies
through their default features. Switch them off and re-enable only what
you need.

```toml
[dependencies]
serde = { version = "1", default-features = false, features = ["derive"] }
tokio = { version = "1", default-features = false, features = [
    "rt-multi-thread",
    "macros",
] }
```

A `cargo tree --edges normal` before and after shows the effect; a
diff of `Cargo.lock` shows the dependency churn the default features
hide.

### Single-feature crates

Some "convenience" crates pull a kitchen sink behind a single useful
function. Inline ten lines of code rather than importing a hundred KB
of transitive dependencies.

### One implementation, one feature flag

When two dependencies provide the same logical capability (TLS, async
runtime, hash algorithm), expose the choice as a feature flag and pick
exactly one. The build that ends up with both is the build that links
two TLS stacks.

## Detect duplication

```bash
cargo tree -d           # show duplicated direct dependencies
cargo tree -d --depth 0 # show only the duplicate roots
```

Common causes:

- a minor-version split between two transitive dependencies,
- a fork held by a single crate that has not caught up,
- feature unification failing because one path requires
  `default-features = false`.

Resolve by raising the lower version in your direct `[dependencies]`,
patching upstream, or filing an issue with the laggard.

## Isolate risk behind features

Treat heavyweight or under-audited dependencies as optional. Expose
their capability behind a feature flag that the binary opts into:

```toml
[features]
default = []
postgres = ["dep:tokio-postgres"]
```

This keeps the trust burden on the consumers who actually want the
capability, and lets `cargo-vet` exemptions narrow naturally.

## Pin the MSRV

```toml
[package]
rust-version = "1.76"
```

Verify in CI on the oldest supported toolchain. `cargo-msrv` can find
the current MSRV when it has drifted; `cargo +1.76.0 build` proves the
declared MSRV still works.

## Record policy in-tree

### `deny.toml`

A minimal starter:

```toml
[advisories]
db-path = "~/.cargo/advisory-db"
db-urls = ["https://github.com/rustsec/advisory-db"]
vulnerability = "deny"
unmaintained = "warn"

[licenses]
allow = ["MIT", "Apache-2.0", "BSD-3-Clause"]
copyleft = "deny"

[bans]
multiple-versions = "warn"
deny = [
    { name = "openssl" },        # use rustls instead
]
```

Run `cargo deny check` in CI and on every PR.

### `supply-chain/`

`cargo-vet`'s home. The two files most worth reviewing in a PR are
`audits.toml` (this project's reviews) and `config.toml` (which peers
it trusts).

## Renovate or Dependabot configuration

- Group patch updates per ecosystem to keep PR noise manageable.
- Hold security advisories in their own PR so they ship faster than
  routine bumps.
- Never auto-merge a dependency PR without a passing `cargo audit`,
  `cargo deny check`, and `cargo vet` run.

## Anti-patterns

- **A `Cargo.lock` change with no PR comment** explaining the diff.
- **An `[patch.crates-io]` block** that exists for a hot fix and never
  gets removed after the upstream fix lands.
- **`cargo update -p <crate>`** run on the release branch without
  re-running the full audit suite.
- **A `forbid(unsafe_code)`** at the workspace level that is silently
  weakened to `deny` because one dependency would not compile.
- **Banning a crate** in `deny.toml` without naming the recommended
  alternative in a comment.
