# Skill Catalogue Status

`skills/` is the active Rust skill catalogue on this branch.

`current-skills/` is retained only as local source material used during the
reduction and rewrite. It is intentionally not part of the committed skill
tree for this branch.

When updating the Rust skill set from this point forward:

- add or revise first-class skills under `skills/`,
- keep long examples and edge cases in `references/`,
- treat `current-skills/` as legacy input, not as the place to extend.

## Catalogue contents

The catalogue is split into a router, six language skills, six
architecture or domain skills, and three deep-dive verification
skills:

- **Router**: `rust-router`.
- **Language**: `rust-memory-and-state`, `rust-types-and-apis`,
  `rust-errors`, `rust-async-and-concurrency`, `rust-unsafe-and-ffi`,
  `rust-performance-and-layout`.
- **Architecture and domain**: `arch-crate-design`,
  `arch-supply-chain`, `arch-decision-records`,
  `domain-web-services`, `domain-cli-and-daemons`,
  `domain-embedded-and-iot`.
- **Verification**: `rust-verification` (routes between tools), with
  deep dives in `proptest`, `kani`, and `verus`.
- **Focused**: `rust-unit-testing` for unit-test helper shape, fixtures,
  parameterization, serialization, and assertions; `rust-unused-code` for
  `dead_code` and `unused_imports` decisions.

`proptest`, `kani`, and `verus` carry larger size envelopes than the
rest because they are procedural deep dives. `proptest` installs as
a regular Cargo dev-dependency; `kani` and `verus` install and run
via [`rust-prover-tools`](https://github.com/leynos/rust-prover-tools)
so the catalogue does not carry forked install scripts.
