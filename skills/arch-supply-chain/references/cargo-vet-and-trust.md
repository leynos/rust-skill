# `cargo-vet` and the decentralised trust model

`cargo-vet` records a fact: a specific crate version has been reviewed
by a specific auditor, against a specific set of criteria. Reviews are
stored in-tree under `supply-chain/`; CI fails if any dependency lacks
an audit, an exemption, or an import from a trusted peer's audit set.

The intent is to make trust an explicit, reviewable, transferable
artifact — not implicit in the act of running `cargo add`.

## Concepts

- **Audit**: a signed claim that the auditor read crate `X` at version
  `Y` and found it met some criteria (default: `safe-to-deploy`).
- **Criteria**: named trust bars (`safe-to-run`, `safe-to-deploy`,
  optional project-specific levels). A diff between two audited
  versions also counts as an audit if the delta is small.
- **Imports**: pull another project's `audits.toml` and trust their
  reviews. Mozilla, Google, Bytecode Alliance, and others publish
  theirs.
- **Exemptions**: temporary "we have not audited this yet" markers, with
  expiry. They allow forward progress without hiding the debt.

## Setup, in three commands

```bash
cargo install cargo-vet
cargo vet init
cargo vet
```

`init` seeds `supply-chain/` and a starter `config.toml`. The bare
`cargo vet` invocation reports the gap: every dependency that lacks
an audit, an import, or an exemption.

## Closing the gap

For each unaudited crate, in priority order:

1. **Import**: if a trusted peer has audited the same version, add their
   `audits.toml` to `config.toml` under `[imports]`.
2. **Audit**: read the source and run `cargo vet certify <crate>
   <version>` to record your review.
3. **Audit a delta**: if you previously audited `1.4.0` and the
   dependency is now `1.4.1`, `cargo vet diff <crate> 1.4.0 1.4.1` shows
   the change; `cargo vet certify` records that the delta is also safe.
4. **Exempt**: if the crate cannot be audited now, add an exemption
   with a deadline. Treat exemptions like TODOs; review them at the
   start of each release cycle.

## Pattern: a minimal `config.toml`

```toml
[cargo-vet]
version = "0.10"

[imports.bytecode-alliance]
url = "https://raw.githubusercontent.com/bytecodealliance/wasmtime/main/supply-chain/audits.toml"

[imports.mozilla]
url = "https://hg.mozilla.org/mozilla-central/raw-file/tip/supply-chain/audits.toml"

[policy."my-crate"]
audit-as-crates-io = true
criteria = "safe-to-deploy"
```

## Pattern: criteria stronger than `safe-to-deploy`

Define project-specific criteria when the default is too weak. Common
additions:

- `crypto-reviewed`: a domain expert has reviewed the cryptographic
  primitive against current best practice.
- `unsafe-reviewed`: every `unsafe` block has been justified and (where
  possible) checked under Miri.
- `no-network`: the crate does not perform network I/O.

Declare them once in `audits.toml`, then require them in `config.toml`
for the dependencies that warrant the stronger bar.

## Anti-patterns

- **Exemption rot.** Exemptions added "for now" and never revisited.
  Set deadlines and run `cargo vet check --no-criteria` to surface
  expired ones.
- **Self-import.** Pulling your own `audits.toml` from another branch
  to silence CI. The trust model breaks the moment auditor and project
  are the same entity.
- **Coarse imports.** Importing every peer's full audit set without
  considering whether their bar matches yours. Pick imports that share
  your criteria, or define delta-criteria mappings.

## Complementary tools

- **`cargo-audit`** queries the [RustSec Advisory Database](https://rustsec.org/)
  for known vulnerabilities. It is necessary but not sufficient:
  advisories cover disclosed CVEs, not unreviewed code.
- **`cargo-deny`** enforces project policy (licence allow-lists, banned
  crates, duplicate-version limits, advisory checks) at the lockfile
  level. Use it for the policy `cargo-vet` cannot express.
- **`cargo-crev`** is `cargo-vet`'s older sibling, with a richer review
  model and a smaller adoption base. Choose `cargo-vet` for new
  projects unless `cargo-crev`'s richer reviews matter to a downstream
  consumer.
