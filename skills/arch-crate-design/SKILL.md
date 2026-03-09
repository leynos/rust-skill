---
name: arch-crate-design
description: Use for Rust crate boundaries, workspace structure, feature flags, public versus internal APIs, layering, and testable module design.
globs: ["**/Cargo.toml", "**/*.rs"]
---

# Rust Crate Design

Use this when the hard part is where a Rust responsibility should live, not
how to write the next function.

## Working stance

- Keep domain logic away from IO, framework glue, and process setup.
- Public crates should expose stable concepts, not convenience shortcuts.
- Prefer thin binaries and reusable libraries.
- Feature flags should add integration or optional capability, not split core
  behaviour into incompatible worlds.
- Tests should follow the same boundaries the design claims to have.

## Decision surface

- New crate: create one when the boundary is stable, reusable, and easier to
  test in isolation.
- New module only: prefer it when the split is still implementation detail.
- Public API: expose the narrow contract, keep helpers and framework types
  internal where possible.
- Feature flag: use it for optional dependencies or integrations, not as a
  substitute for design decisions.

## Red flags

- binaries contain most of the business logic,
- public types expose runtime or framework internals,
- one crate imports everything because boundaries are nominal only,
- feature combinations create meaningfully different programs,
- integration tests must reach through layers to set up basic scenarios.
