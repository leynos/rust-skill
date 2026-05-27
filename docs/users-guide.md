# rust-skill users' guide

This guide explains how to use the Rust skill catalogue in day-to-day Rust
work: where to install it, how to invoke skills, how the router decides which
skill to load, and what each newly-added verification, supply-chain, and
decision-record skill is for.

The companion document [`skill-catalogue-status.md`](skill-catalogue-status.md)
lists the catalogue contents and tier shape. This guide is the operator-facing
counterpart.

## What the catalogue is

`skills/` holds a compact set of Rust skills designed to be loaded one or two
at a time. Each `SKILL.md` is intentionally short, with longer comparison
material in `references/`. The router (`rust-router`) directs traffic so that
callers do not load half the catalogue when one skill will do.

The tiers are:

- one **router** — `rust-router`,
- six **language** skills — memory and state, types and APIs, errors,
  async and concurrency, unsafe and FFI, performance and layout,
- six **architecture and domain** skills — crate design, supply chain,
  decision records, web services, CLIs and daemons, embedded and IoT,
- one **verification router** — `rust-verification` — and two deep dives,
  `kani` and `verus`,
- one **focused** skill — `rust-unused-code` for `dead_code` and
  `unused_imports` decisions.

## Installing the catalogue

The catalogue ships as a directory of skill folders. Copy them into the
Codex skills location:

```bash
mkdir -p ~/.codex/skills
cp -a skills/* ~/.codex/skills/
```

Re-run the copy when the catalogue is updated; skills are plain text and
overwriting is safe.

The two deep-dive skills, `kani` and `verus`, do not install their tools
themselves. They delegate to
[`rust-prover-tools`](https://github.com/leynos/rust-prover-tools), which
exposes a single CLI for both:

```bash
prover-tools kani install
prover-tools verus install
```

Use `prover-tools kani check-version` and `prover-tools verus run
--proof-file path/to/file.rs` for the everyday loops. The catalogue does
not carry forked install scripts; the deep dives reference the tool by
name only.

## Invoking skills

Skills are addressed by name. The router is the usual entry point:

```text
Use $rust-router to route this Rust task, then help me untangle a
borrow-checker error in this handler.
```

When the pressure point is already obvious, call the relevant skill
directly:

```text
Use $rust-errors to review this error enum for a publishable library
crate.
```

The router is cheap to load. When a task spans more than one area —
say, an async handler that also needs error-type advice — load the
router first and let it pick the pairing.

## How the router decides

`rust-router` routes by the concrete problem in front of you, not by
the file you happen to be editing. A short version of its decision
table:

- ownership, borrowing, aliasing, or interior mutability →
  `rust-memory-and-state`,
- trait bounds, generics, API shape, newtypes, or typestate →
  `rust-types-and-apis`,
- error shape, panic boundary, or library-versus-binary handling →
  `rust-errors`,
- tasks, `Send`/`Sync`, blocking, channels, or cancellation →
  `rust-async-and-concurrency`,
- allocation pressure, layout, or benchmark discipline →
  `rust-performance-and-layout`,
- `unsafe`, FFI, layout guarantees, or soundness review →
  `rust-unsafe-and-ffi`,
- crate boundaries, features, public surface, or layering →
  `arch-crate-design`,
- dependency hygiene, `cargo-vet`, `cargo-deny`, SemVer guardrails →
  `arch-supply-chain`,
- recording a hard-to-reverse architectural decision (Y-Statement) →
  `arch-decision-records`,
- choosing a verification tool (Miri, proptest, `cargo-mutants`, `loom`,
  `shuttle`, `turmoil`, Kani, Verus) → `rust-verification`,
- HTTP services, middleware, or request state → `domain-web-services`,
- CLIs, workers, daemons, or long-running jobs →
  `domain-cli-and-daemons`,
- `no_std`, firmware, devices, or edge nodes →
  `domain-embedded-and-iot`.

The router's pairing rules and escalation triggers live in its
`SKILL.md`; the
[routing matrix](../skills/rust-router/references/routing-matrix.md)
covers the residual ambiguous cases.

## When to reach for the new skills

The recent catalogue extension introduces five entry points covering
verification, supply chain, and decision records. The short versions:

### `rust-verification` — pick the right adversarial tool

Use this skill when you need to prove or disprove a property and are
unsure whether to reach for Miri, sanitizers, property tests,
`cargo-mutants`, `loom`, `shuttle`, `turmoil`, Kani, or Verus. The
skill's selection table maps failure modes to tools. From there it
routes into the `kani` and `verus` deep dives.

### `kani` — bounded model checking

Use this skill when writing a harness for a small, well-bounded
property: an arithmetic invariant, a parser corner case, or a state
machine with a small alphabet. Kani is unwind-bounded by default;
the skill describes how to set `#[kani::unwind(n)]`, when to use
`kani::any` and `kani::assume`, and when to escalate to Verus instead.

### `verus` — deductive verification

Use this skill when the property must hold for unbounded inputs, when
the bounded loop in Kani times out, or when the proof composes
several lemmas. The skill covers `spec`/`proof`/`exec` mode
discipline, trigger heuristics for the underlying Z3 solver, the
`broadcast use` pattern for sequence axioms, and the layout of a
proof project that mirrors a production module.

### `arch-supply-chain` — dependency hygiene and audits

Use this skill when adding a dependency, tightening a lockfile policy,
configuring `cargo-vet` or `cargo-deny`, or wiring SemVer guardrails
(`cargo-semver-checks`, `cargo-public-api`) into release. The
references describe a decentralized audit setup with imports from
the Bytecode Alliance and Mozilla, plus a `deny.toml` policy template.

### `arch-decision-records` — Y-Statement ADRs

Use this skill when capturing a decision that is hard to reverse —
a typestate, an `unsafe` invariant, a verification-tool choice, a
public API shape. The skill gives the six-clause Y-Statement template
and three worked Rust examples, and explains how to supersede an
earlier ADR cleanly.

## Working stance for the catalogue

A few habits make the catalogue earn its keep:

- **Route before you load.** A short prompt to `rust-router` costs
  little and avoids loading skills you will not use.
- **Prefer one language skill plus at most one domain or architecture
  skill** for any single task.
- **Stop when the answer is turning into a tutorial.** Cut back to the
  decision that actually matters and the skill that owns it.
- **Treat verification as a layered investment.** Miri and proptest
  pay off early; Kani and Verus pay off when the property is small,
  load-bearing, and hard to test by example.
- **Record the decision, not the discussion.** ADRs are for the
  hard-to-reverse parts; routine choices belong in code review.

## Further reading

- [Skill catalogue status](skill-catalogue-status.md) — what is active
  and what is legacy input.
- [Reduction execplan](execplans/reduced-skill-footprint.md) — the
  original rewrite plan and validation history.
- [Advanced encapsulation and verification execplan](execplans/advanced-encapsulation-and-verification.md)
  — the plan for the verification, supply-chain, and decision-record
  extension.
- [`rust-router` SKILL.md](../skills/rust-router/SKILL.md) — the
  authoritative routing rules.
- [Routing matrix](../skills/rust-router/references/routing-matrix.md)
  — the table the router falls back to for ambiguous cases.
- [`CHANGELOG.md`](../CHANGELOG.md) — what changed in each release
  of the catalogue.
