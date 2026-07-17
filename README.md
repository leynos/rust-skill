# rust-skill

*A compact Rust skill catalogue for Codex, shaped to help with real Rust work
without drowning out the work itself.*

This repository rebuilds a large inherited skill set into a smaller, sharper
collection of Rust skills. It keeps the useful decision surfaces, drops a lot
of repeated boilerplate, and leans on short first-class skills with references
for the longer edge cases.

______________________________________________________________________

## Why rust-skill?

- **Smaller default load**: The committed `skills/` tree is much lighter than
  the original local source material.
- **Rust-specific judgement**: The catalogue focuses on ownership, APIs,
  errors, async, performance, unsafe code, and crate design.
- **Clear routing**: `rust-router` directs to the smallest useful skill
  instead of loading half the catalogue at once.
- **Practical tone**: The skills aim to sound like a helpful technical lead,
  not a life coach with a megaphone.

______________________________________________________________________

## Quick start

### Installation

```bash
mkdir -p ~/.codex/skills
cp -a skills/* ~/.codex/skills/
```

### Basic usage

```text
Use $rust-router to route this Rust task, then help me fix an E0382 moved-value
error in my handler.
```

When the pressure point is already known, call the skill directly:

```text
Use $rust-errors to review this error enum for a publishable library crate.
```

______________________________________________________________________

## Features

- One router, six language skills, and six domain or architecture skills.
- Focused testing and cleanup guidance for Rust unit-test shape and unused
  code decisions.
- Short `SKILL.md` files, with references for the longer comparison material.
- Coverage for crate design, web services, CLI and daemon work, and embedded
  or IoT work.
- Packaging guidance for workspaces, publishability, helper crates, and
  `cargo-binstall`.
- Verification, supply-chain, and decision-record skills for the advanced
  "impeccable software" stance: Miri, proptest, `cargo-mutants`, `loom`,
  `shuttle`, `turmoil`, Kani, and Verus on one side; `cargo-vet`,
  `cargo-deny`, SemVer guardrails, and Y-Statement ADRs on the other.
  Deep dives for `proptest`, `kani`, and `verus` cover strategy design,
  harness shape, and proof discipline respectively.
- A focused `nll-to-polonius` migration skill for adopting the Polonius borrow
  checker, retiring confirmed NLL workarounds, and evolving internal APIs
  towards borrow-centric designs where compatibility permits.
- English-only rewrites of the new catalogue, with the older tree retained as
  local source material.

______________________________________________________________________

## Learn more

- [Users' guide](docs/users-guide.md) — installation, invocation, routing,
  and when to reach for the verification, supply-chain, and decision-record
  skills
- [Skill catalogue status](docs/skill-catalogue-status.md) — what is active and
  what is legacy input
- [Reduction execplan](docs/execplans/reduced-skill-footprint.md) — design,
  rationale, and validation history for the rewrite
- [Rust router](skills/rust-router/SKILL.md) — the main entry point
- [Crate design](skills/arch-crate-design/SKILL.md) — workspace, packaging, and
  release-shape guidance
- [NLL to Polonius](skills/nll-to-polonius/SKILL.md) — Polonius adoption,
  workaround audits, and borrow-centric API evolution

______________________________________________________________________

## Acknowledgements

This repository is principally inspired by two generous MIT-licensed Rust skill
collections:

- [Leonardo Maldonado's `rust-skills`](https://github.com/leonardomso/rust-skills)
- [Zhang Han Dong's `rust-skills`](https://github.com/actionbook/rust-skills)

This rewrite does not copy those repositories wholesale. It adapts the idea to
this smaller Codex-oriented catalogue and keeps the resulting repository under
the MIT licence as well.

______________________________________________________________________

## Licence

MIT — see [LICENSE](LICENSE) for details.

______________________________________________________________________

## Contributing

Contributions are welcome. Keep new material under `skills/`, prefer short
first-class skills with references for longer detail, and treat
`current-skills/` as local source input rather than the place to extend.
