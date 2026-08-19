# Documentation strategy

A Polonius migration changes what "correct Rust" looks like inside one
repository while much of the wider ecosystem's habits, tutorials, and coding
agents' training data still reflect NLL. Undocumented, the migration erodes:
the next contributor or agent sees a §1.1 direct form, recognizes it as "the
thing the borrow checker rejects", and helpfully regresses it to a double
lookup. The documentation's job is to make the new forms legible as
deliberate.

## 1. Toolchain requirement: README and CONTRIBUTING

State the requirement where build instructions live, with the reason. For a
project pinned to a current nightly:

> This crate requires Polonius Alpha and pins a current Rust nightly in
> `rust-toolchain.toml`. Alpha is the nightly default; do not opt out with
> `-Zpolonius=off`. Several functions use single-lookup get-or-insert and
> conditional borrow-return forms that NLL rejects; see `docs/polonius.md`
> for the pattern inventory. Stable Rust will report borrow errors in these
> functions until Alpha stabilizes. They are expected and not bugs.

For a project pinned to an older nightly and selecting Alpha explicitly,
document `-Zpolonius=next` and why the older toolchain remains pinned. Do not
teach current-nightly users that the flag is universally required.

For prepare-only crates, invert the guidance: document that
`POLONIUS-CANDIDATE` tags exist, what they mean, and that the tagged
workarounds must not be "simplified" until the toolchain policy changes.

## 2. Site-level comment convention

Use one greppable tag family at every rewritten or annotated site:

```rust
// POLONIUS(case-3): direct get-or-insert; single lookup on hit, key
// cloned only on miss. Rejected by NLL; do not restructure to entry()
// or contains_key.
```

```rust
// POLONIUS-CANDIDATE(lending-iter): rewrite to conditional borrow-return
// when Polonius Alpha stabilizes. Tracked in docs/polonius.md.
```

```rust
// POLONIUS-REFUSED(aliasing): this clone breaks a simultaneous borrow;
// Polonius does not change this. Audited 2026-08.
```

The `REFUSED` tag matters as much as the others: it pre-empts the next audit
re-litigating W1-style sites. Keep the taxonomy small: `case-3`,
`lending-iter`, `scan-mutate`, `aliasing`, and `flow-sensitivity`, matching
the pattern catalogue's section names so the tags index into it.

## 3. Tracking document: docs/polonius.md

Keep one page with four tables:

1. rewritten sites (file, pattern, date, compiler version verified against);
2. API evolution targets (owning API, target signature, playbook shape,
   status);
3. candidates awaiting stabilization;
4. refusals with the constraint named (aliasing, suspension point,
   id-is-data, or flow-sensitivity).

Link each row to the pattern catalogue or playbook section rather than
re-explaining it. This is the artefact a future stabilization-day pass works
through mechanically. Refusal rows ensure that pass starts from conclusions
rather than re-running the argument.

## 4. Agent guidance: CLAUDE.md / AGENTS.md

Coding agents are especially likely to regress the migration because their
priors encode NLL's rejections as facts about Rust. Add an explicit block:

```markdown
## Borrow checking

This repository compiles under Polonius Alpha using the pinned project
toolchain. Current nightly enables Alpha by default.

- Code tagged `POLONIUS(...)` uses forms that NLL rejects. They are correct
  here. Never rewrite them into double lookups, `entry()` with cloned keys,
  index-returning helpers, or precomputed error context.
- When writing new code, prefer the direct forms in `docs/polonius.md` §1
  over defensive workarounds. Do not add clones whose only purpose is to end
  a borrow without first checking whether the direct form compiles.
- When designing new internal APIs, default to borrow-centric signatures:
  lookups and get-or-create accessors return references; ids are reserved for
  persisted or cross-boundary identity; error context is built lazily in the
  failure arm. See `docs/polonius.md` for the target shapes and the
  constraints where owned values remain correct.
- Polonius does not permit simultaneous borrows or every loop-carried
  conditional reborrow. Do not remove clones or restructures tagged
  `POLONIUS-REFUSED`.
- Verify borrow-sensitive changes with the project's normal `cargo check`.
  To classify whether a form genuinely requires Alpha, repeat on nightly with
  `RUSTFLAGS="${RUSTFLAGS:+$RUSTFLAGS }-Zpolonius=off" cargo check`.
  Omitting `-Zpolonius=next` is not an NLL control on current nightly.
```

## 5. Changelog and review checklist

- Changelog: record the compiler requirement and link `docs/polonius.md`.
  Downstream users pinning toolchains need this more than they need the
  pattern details.
- Code-review checklist: require a `POLONIUS-REFUSED` justification or a
  failed NLL-control compile before a new borrow-checker workaround lands.

## 6. Editor and CI configuration notes

Pin the same Alpha-capable toolchain in local development, CI, and editor
Cargo invocations. Current nightly needs no extra flag to enable Alpha, and
rust-analyzer normally inherits the project toolchain through Cargo.

If a project deliberately carries `-Zpolonius=next` for an older nightly or
`-Zpolonius=off` as an opt-out, keep the flag in checked-in
`.cargo/config.toml` or the editor's Cargo environment. Otherwise
command-line and editor diagnostics diverge, red squiggles appear on accepted
code, and contributors "fix" it back into defensive NLL forms.
