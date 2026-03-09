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
- **Clear routing**: `rust-router` points you to the smallest useful skill
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

If you already know the pressure point, call the skill directly:

```text
Use $rust-errors to review this error enum for a publishable library crate.
```

______________________________________________________________________

## Features

- One router, six language skills, and four domain or architecture skills.
- Short `SKILL.md` files, with references for the longer comparison material.
- Coverage for crate design, web services, CLI and daemon work, and embedded
  or IoT work.
- Packaging guidance for workspaces, publishability, helper crates, and
  `cargo-binstall`.
- English-only rewrites of the new catalogue, with the older tree retained as
  local source material.

______________________________________________________________________

## Learn more

- [Skill catalogue status](docs/skill-catalogue-status.md) — what is active and
  what is legacy input
- [Reduction execplan](docs/execplans/reduced-skill-footprint.md) — design,
  rationale, and validation history for the rewrite
- [Rust router](skills/rust-router/SKILL.md) — the main entry point
- [Crate design](skills/arch-crate-design/SKILL.md) — workspace, packaging, and
  release-shape guidance

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
