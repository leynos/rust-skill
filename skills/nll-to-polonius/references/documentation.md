# Documentation strategy

A Polonius migration changes what "correct Rust" looks like inside one
repository while the wider ecosystem's habits, lints, tutorials, and — most
acutely — coding agents' training data still reflect NLL. Undocumented,
the migration erodes: the next contributor or agent sees a §1.1 direct
form, recognizes it as "the thing the borrow checker rejects", and
helpfully regresses it to a double lookup. The documentation's job is to
make the new forms legible as deliberate.

## 1. Toolchain requirement — README and CONTRIBUTING

State the requirement where build instructions live, with the reason:

> This crate requires the Polonius borrow-checking analysis
> (`-Zpolonius=next`, nightly), configured in `.cargo/config.toml`. Several
> functions use single-lookup get-or-insert and conditional borrow-return
> forms that NLL rejects; see docs/polonius.md for the pattern inventory.
> Plain `cargo check` on stable will report borrow errors in these
> functions — they are expected and not bugs.

For prepare-only crates, invert it: document that POLONIUS-CANDIDATE tags
exist, what they mean, and that the tagged workarounds must not be
"simplified" until the toolchain policy changes.

## 2. Site-level comment convention

One greppable tag family, applied at every rewritten or annotated site:

```rust
// POLONIUS(case-3): direct get-or-insert; single lookup on hit, key
// cloned only on miss. Rejected by NLL — do not restructure to entry()
// or contains_key.
```

```rust
// POLONIUS-CANDIDATE(lending-iter): rewrite to conditional borrow-return
// when -Zpolonius=next stabilizes. Tracked in docs/polonius.md.
```

```rust
// POLONIUS-REFUSED(aliasing): this clone breaks a simultaneous borrow;
// Polonius does not change this. Audited 2026-07.
```

The REFUSED tag matters as much as the others: it pre-empts the next audit
re-litigating W1-style sites. Keep the taxonomy small — case-3,
lending-iter, scan-mutate, aliasing, flow-sensitivity — matching the
pattern catalogue's section names so the tags index into it.

## 3. Tracking document — docs/polonius.md

One page, four tables: rewritten sites (file, pattern, date, nightly
version verified against), API evolution targets (owning API, target
signature, playbook shape, status), candidates awaiting stabilization, and
refusals with the constraint named (aliasing, suspension point,
id-is-data, flow-sensitivity). Link each row to the pattern catalogue or
playbook section rather than re-explaining. This is the artefact a future
"stabilization day" or next evolution pass works through mechanically —
refusal rows exist so that pass starts from conclusions rather than
re-running the argument.

## 4. Agent guidance — CLAUDE.md / AGENTS.md

Coding agents are the population most likely to regress the migration,
because their priors encode NLL's rejections as facts about Rust. Add an
explicit block:

```markdown
## Borrow checking

This repository compiles under Polonius (`-Zpolonius=next`). Consequences:

- Code tagged `POLONIUS(...)` uses forms that NLL rejects. They are
  correct here. Never rewrite them into double lookups, `entry()` with
  cloned keys, index-returning helpers, or precomputed error context.
- When writing new code, prefer the direct forms in docs/polonius.md §1
  over defensive workarounds. Do not add clones whose only purpose is to
  end a borrow without first checking whether the direct form compiles.
- When designing new internal APIs, default to borrow-centric signatures:
  lookups and get-or-create accessors return references; ids are reserved
  for persisted or cross-boundary identity; error context is built lazily
  in the failure arm. See docs/polonius.md for the target shapes and the
  constraints (aliasing, suspension points, struct-field lifetimes) where
  owned values remain correct.
- Polonius does not permit simultaneous borrows or loop-carried
  conditional reborrows. Do not remove clones or restructures tagged
  `POLONIUS-REFUSED`.
- Verify borrow-sensitive changes with
  `RUSTFLAGS="-Zpolonius=next" cargo +nightly check`, not stable
  `cargo check`.
```

## 5. Changelog and review checklist

- Changelog: one entry stating the new compiler requirement and linking
  docs/polonius.md — downstream users pinning toolchains need this more
  than they need the pattern details.
- Code-review checklist (if the repository keeps one): add "borrowck
  workarounds require a POLONIUS-REFUSED justification or a failed compile
  under the flag" so new defensive patterns cannot land silently.

## 6. Editor and CI configuration notes

Document, adjacent to the toolchain requirement, that rust-analyzer needs
the flag (via `rust-analyzer.cargo.extraEnv` or the checked-in
`.cargo/config.toml`) — otherwise contributors see red squiggles on
correct code and "fix" them, which is the regression vector §4 guards
against arriving through the editor instead of the agent.
