---
name: arch-decision-records
description: Capture architectural decisions in Rust projects using the Y-Statement format. Use when a choice is hard to reverse, when the rationale will outlive its author, or when reviewers keep asking "why did we pick this?". Especially relevant for typestate, trait bounds, public API shape, `unsafe` invariants, runtime selection, and verification tooling.
---

# Architecture Decision Records for Rust

An Architecture Decision Record (ADR) captures one decision and the
reason behind it. ADRs exist so that six months later, when the
original engineer has left or forgotten, the next reader can rebuild
the constraints rather than guess at them.

In Rust, decisions worth recording tend to encode invariants the
compiler is already enforcing — typestate edges, trait bounds, lifetime
annotations, `unsafe` contracts. The ADR is the cover letter the type
signature cannot carry.

## Working stance

- Write the ADR at the moment the decision becomes hard to reverse,
  not after the next release.
- Use the Y-Statement template so the structure is uniform across the
  repository.
- Number ADRs sequentially; never renumber.
- An ADR is immutable. Supersede it with a new ADR; do not edit the
  superseded one beyond a "Superseded by ADR-NNN" header.
- Keep ADRs in-tree under `docs/adr/` (or similar). They are reviewable
  code-adjacent artefacts.

## When to write one

Write an ADR when any of the following is true:

- A reviewer asks "why did we choose this over X?" for the second time.
- The decision changes the public API of a published crate.
- The decision encodes a soundness invariant in `unsafe` code.
- The decision picks one of several plausible runtimes, error types,
  serialisation formats, or verification tools.
- The decision introduces a load-bearing typestate machine or
  trait-object boundary.

Do not write an ADR for ordinary refactors, bug fixes, or local
implementation choices.

## The Y-Statement template

```text
In the context of <use case>,
facing <concern>,
we decided for <option>,
and against <alternatives>,
to achieve <quality>,
accepting <downside>.
```

Six clauses, no more. Each clause is a sentence; the whole record is
typically under a page. See
[`references/y-statement-template.md`](references/y-statement-template.md)
for a fully worked example and three Rust-specific variations.

## File shape

```text
docs/adr/0001-use-rustls-not-openssl.md
docs/adr/0002-typestate-for-request-builder.md
docs/adr/0003-verus-for-edge-ordering-proof.md
```

Each file:

- starts with the ADR number, title, status, and date,
- holds exactly one Y-Statement,
- ends with a "Consequences" section: at most three bullets describing
  what changes downstream.

## Red flags

- ADRs are written after the fact and rationalise a decision rather
  than document it.
- ADRs accumulate "Superseded" stamps without superseding records.
- The Y-Statement's "against" clause is empty — no alternative was
  considered.
- The "accepting" clause is empty — no downside was named.
- An ADR repeats the contents of a SemVer changelog. ADRs explain
  motivation; changelogs record what changed.
- Multiple ADRs describe the same decision from different angles.
  Consolidate or supersede.

## Cross-references

- Rust-specific worked examples and template:
  [`references/y-statement-template.md`](references/y-statement-template.md).
- Crate-shape decisions live next door:
  [`arch-crate-design`](../arch-crate-design/SKILL.md).
- Verification tool choice often warrants its own ADR:
  [`rust-verification`](../rust-verification/SKILL.md).
