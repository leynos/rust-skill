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
- one **verification router** — `rust-verification` — and three deep dives,
  `proptest`, `kani`, and `verus`,
- two **focused** skills — `rust-unit-testing` for unit-test shape and
  assertions, and `rust-unused-code` for `dead_code` and `unused_imports`
  decisions,
- one **migration** skill — `nll-to-polonius` for adopting the Polonius borrow
  checker and retiring designs imposed by non-lexical lifetime (NLL)
  limitations.

## Installing the catalogue

The catalogue ships as a directory of skill folders. Copy them into the
Codex skills location:

```bash
mkdir -p ~/.codex/skills
cp -a skills/* ~/.codex/skills/
```

Re-run the copy when the catalogue is updated; skills are plain text and
overwriting is safe.

Each skill directory is named after the `name` in its `SKILL.md` manifest, and
that `name` is the discovery name a strict loader uses. The two must agree: a
manifest without a `name`, or one that disagrees with its directory, is not
discoverable. The copy itself performs no validation; `make lint` is the
contributor gate that validates every shipped manifest before it is published,
so a malformed or non-conformant manifest fails there rather than reaching a
reader's skills directory.

The `proptest` deep dive is a regular Cargo dev-dependency; the
relevant lines for `Cargo.toml` and the recommended optional crates
(`proptest-derive`, `test-strategy`, `proptest-state-machine`) live
in its skill.

The `kani` and `verus` deep dives delegate tool installation to
[`rust-prover-tools`](https://github.com/leynos/rust-prover-tools),
which exposes a single CLI for both:

```bash
prover-tools kani install
prover-tools verus install
```

Use `prover-tools kani check-version` and `prover-tools verus run
--proof-file path/to/file.rs` for the everyday loops. The catalogue does
not carry forked install scripts; the deep dives reference the tool by
name only.

## Invoking skills

`rust-router` remains available for implicit invocation, so Codex can select it
when a Rust task matches its description. The other 19 skills are
explicit-only: they stay out of the default model context unless a user or
agent specifically asks for one.

Skills are addressed by name. The router is the usual entry point:

```text
Use $rust-router to route this Rust task, then help me untangle a
borrow-checker error in this handler.
```

When the pressure point is already obvious, invoke the relevant specialist
directly with its `$skill-name`:

```text
Use $rust-errors to review this error enum for a publishable library
crate.
```

The router is cheap to load. When a task spans more than one area —
say, an async handler that also needs error-type advice — load the
router first and let it pick the pairing.

## How the router decides

`rust-router` routes by the concrete problem at hand, not by the file
being edited. A short version of its decision table:

- ownership, borrowing, aliasing, or interior mutability →
  `rust-memory-and-state`,
- Polonius adoption, NLL workaround audits, borrow-checker-driven defensive
  clones, or borrow-centric API evolution → `nll-to-polonius`,
- trait bounds, generics, API shape, newtypes, or typestate →
  `rust-types-and-apis`,
- error shape, panic boundary, or library-versus-binary handling →
  `rust-errors`,
- unit-test fixtures, table tests, assertion helper refactors, snapshots,
  or serialized tests → `rust-unit-testing`,
- `dead_code`, `unused_imports`, feature-gated reachability, or uncertain
  unused-item removal → `rust-unused-code`,
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

## Testing hierarchy

Pick the first level whose evidence matches the question:

1. **Named unit test**: one scenario, regression, exact output, or
   error contract matters.
2. **Parameterized `rstest` table**: a finite truth table, standards
   corpus, or set of cases whose rows each carry semantic meaning.
3. **Lightweight `proptest`**: one round trip, invariant, oracle, or
   metamorphic relation should hold across many cheap, repeatable
   inputs. A growing set of representative `#[case]` rows is the usual
   signal, and the estate's reviewers flag it as such.
4. **Structured or stateful `proptest`**: valid data has dependent or
   recursive structure, or failures depend on operation history.
5. **Kani**: a small bounded function needs exhaustive exploration of
   every reachable path within a stated bound.
6. **Verus**: the property must hold with no bound, over a small stable
   pure kernel.

`cargo-mutants` sits beside the hierarchy. Use it when the question is
whether the current suite would notice a plausible defect. Miri sits
below it, on the tests that already touch `unsafe`.

Leave the hierarchy for scheduling, integration, load, performance, or
foreign-code failures. Those need `loom`, `shuttle`, or `turmoil`, real
or simulated boundaries, benchmarks and profilers, or sanitizers.
`rust-verification` is the escalation selector when the rung is
unclear; a clear lightweight invariant goes straight to `proptest`.

## When to reach for the new skills

The recent catalogue extensions cover verification, supply chain, decision
records, and Polonius migration. The short versions:

### `nll-to-polonius` — migrate beyond NLL constraints

Use this skill when adopting `-Zpolonius=next`, auditing code for confirmed
NLL workarounds, or redesigning internal lookup and caching APIs around
returned borrows. It distinguishes lifetime limitations that Polonius can
remove from aliasing, async, and thread-boundary constraints that still
require ownership. Routine borrow errors continue to route to
`rust-memory-and-state`.

### `rust-verification` — pick the right adversarial tool

Use this skill when you need to prove or disprove a property and are
unsure whether to reach for Miri, sanitizers, property tests,
`cargo-mutants`, `loom`, `shuttle`, `turmoil`, Kani, or Verus. The
skill's selection table maps failure modes to tools. From there it
routes into the `proptest`, `kani`, and `verus` deep dives.

### `proptest` — property-based testing

Use this skill when a pure function has a property (round-trip,
idempotence, ordering, conservation) that is easier to state than to
enumerate, or when a parser or codec must round-trip across all
valid inputs. The skill covers strategy design with `prop_compose!`,
the filtering trap and its fix, regression-file discipline,
state-machine tests via `proptest-state-machine`, and the
`proptest-derive` vs `test-strategy` choice. It also answers the
question reviewers ask first, whether a change needs a property test at
all, and ships a review checklist and a sibling-module template drawn
from the estate's review history.

### `rust-unit-testing` — unit-test shape and assertions

Use this skill when ordinary Rust unit tests need clearer structure:
`rstest` fixtures and parameterized cases, fallible setup helpers,
`serial_test` for genuine global-state isolation, rich matcher assertions
with `googletest`, diff-friendly equality with `pretty_assertions`, and
snapshot tests with `insta`. It also carries a worked example for splitting
one mixed assertion helper into extraction, pure comparison, and a thin
assertion wrapper.

### `kani` — bounded model checking

Use this skill when writing a harness for a small, well-bounded
property: an arithmetic invariant, a parser corner case, or a state
machine with a small alphabet. Kani is unwind-bounded by default;
the skill describes how to set `#[kani::unwind(n)]`, when to use
`kani::any` and `kani::assume`, and when to escalate to Verus instead.
Its references carry the project on-ramp (pins, Makefile targets that
delegate to `prover-tools`, smoke and nightly CI, contract tests) and
the review checklist for vacuous harnesses, model drift, solver
cliffs, and the `cfg(kani)` build.

### `verus` — deductive verification

Use this skill when the property must hold for unbounded inputs, when
the bounded loop in Kani times out, or when the proof composes
several lemmas. The skill covers `spec`/`proof`/`exec` mode
discipline, trigger heuristics for the underlying Z3 solver, the
`broadcast use` pattern for sequence axioms, and the layout of a
proof project that mirrors a production module, including the
refinement lemma that binds an idealized spec to the runtime structure.
Its references carry the on-ramp and review checklist.

The survey these checklists come from is
[`docs/verification-review-failure-modes.md`](verification-review-failure-modes.md).

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
