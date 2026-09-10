---
name: rust-verification
description: Select and combine Rust verification tools — Miri, sanitizers, property testing, mutation testing, deterministic concurrency exploration (loom, shuttle, turmoil), bounded model checking (Kani), and deductive proofs (Verus). Use when choosing the smallest tool that gives the required guarantee for a given failure mode.
---

# Rust verification: choosing the right adversary

Tests show a program works on the inputs you tried. Verification tools
attack the program with adversaries chosen by failure mode: UB,
unexpected inputs, schedule chaos, logic gaps, exhaustive state, or
unbounded reasoning. Pick the smallest adversary that fits the property
at risk.

Use this skill when the required evidence is unclear or the task has
outgrown ordinary examples and a lightweight property. Do not insert a
selector ceremony between a clear, cheap invariant and a ten-line
`proptest!` block; load `proptest` directly for that case.

The tools here answer different questions. They form an escalation map,
not a single scale from weak to strong.

## Before escalating

- One named scenario, exact output, or finite normative table belongs in
  `rust-unit-testing`.
- One invariant over a broad, cheap, repeatable input space belongs
  directly in `proptest`.
- Load this selector when valid data needs a substantial model, operation
  history matters, every reachable path within a bound matters, the
  property has no bound at all, or the question is whether the suite would
  detect wrong code.

## The questions each tool answers

- **Miri and sanitizers**: *Does the code the tests already run commit
  undefined behaviour?*
- **`proptest`**: *Does this property hold across a generated input
  space?* Generation with shrinking is the cheapest adversary for round
  trips, idempotence, oracles, invariants, and metamorphic relations; its
  advanced forms cover dependent data, recursive structures, and operation
  histories.
- **`loom`, `shuttle`, `turmoil`**: *Is there a schedule under which this
  breaks?*
- **`kani`**: *Is there an input within this bound that violates the
  assertion?* Symbolic execution over every path in a stated bound,
  reporting a concrete counter-example.
- **`verus`**: *Does this hold for every input, with no bound?* A
  deductive proof over a pure kernel, discharged by Z3.
- **`cargo-mutants`**: *Would the test suite notice if the production code
  were wrong?* It measures test sensitivity, not program correctness.

## Working stance

- Name the failure mode before naming the tool.
- Each tool is additive: Miri does not replace proptest, Kani does not
  replace Verus.
- Run cheap adversaries on every change; reserve expensive sweeps for
  code where they pay back.
- The effort is not finished until a deliberate mutation of the
  production code is caught by it.

## Selection by failure mode

| Failure mode                                          | First reach        |
| ----------------------------------------------------- | ------------------ |
| Undefined behaviour in `unsafe` (aliasing, init, UB)  | Miri + sanitizers  |
| Input gaps in pure functions                          | `proptest`         |
| "My tests pass but my logic is wrong"                 | `cargo-mutants`    |
| Async cancellation, ordering, partial-failure         | `turmoil`          |
| Atomic / lock-free memory ordering on a single core   | `loom`             |
| Mutex / channel scheduling on a single core           | `shuttle`          |
| Structural invariant over a bounded state space       | `kani`             |
| Algebraic property over an unbounded domain           | `verus`            |

See [`references/tool-selection.md`](references/tool-selection.md) for a
longer walkthrough with one paragraph per tool.

## Layering rule

Climb only when the layer below is clean; bugs found higher up are much
harder to diagnose.

1. Unit tests anchor concrete expectations.
2. Miri and sanitizers catch UB on the inputs tests already exercise.
3. `proptest` widens inputs; `cargo-mutants` checks the tests can fail.
4. `loom`, `shuttle`, and `turmoil` shake the schedule.
5. `kani` proves bounded structural invariants.
6. `verus` proves unbounded algebraic properties.

## What none of them establish

- A passing generated or bounded search is not a proof outside the
  explored domain and bound; a passing Verus proof says nothing about
  code its spec mirror has drifted from.
- Race conditions and ordering bugs need schedule-aware tools, not more
  cases.
- Resource leaks under load need load tests and profilers.
- Foreign-code faults need sanitizers or native fuzzers.
- Architectural mistakes survive when the contract itself is wrong.

## Combining the tools

Use combinations only when the questions are orthogonal. A common shape
is named unit tests plus lightweight `proptest` on every CI run, Miri on
the `unsafe` tests in the same run, a curated Kani smoke tier on pull
requests with the full harness set nightly, Verus on a schedule or on
demand once proofs are stable, and `cargo-mutants` as a nightly or
pre-release suite audit. Do not run all of them merely because all of
them are installed; match cadence and cost to the assurance question,
and state that question in the CI job's name or comment.

## Deterministic chaos

`loom`, `shuttle`, `turmoil`, and `kani` require the system under test
to be deterministic given its inputs. Hidden non-determinism (clocks,
RNG, thread IDs, env reads) breaks reproduction. See
[`references/deterministic-chaos.md`](references/deterministic-chaos.md)
for the fences chaos tools require.

## When reviewers expect verification

Across the estate, code review applies one trigger: a property test or
a bounded model checker is expected when a change introduces an
invariant over a range of inputs, states, orderings, or transitions.
Parsers, canonicalizers, merge and precedence rules, bounded queues,
validators, and any `unsafe` block with a caller-upheld invariant
qualify. CodeRabbit's pre-merge "Testing (Property / Proof)" check
fires as a warning, repeats every round until satisfied, and treats a
PR body that claims coverage it does not have as a defect. The survey
behind this rule found that the single most common review event on
verification work is a missing property test, not a wrong one.

Answer the trigger explicitly, in one of three ways:

1. land the property test, harness, or proof in the same PR;
2. defer it to a tracked issue and say so in the PR;
3. write a short scope statement explaining why the domain is small,
   finite, and enumerated in full on every build, so a generator adds
   nothing.

Silence, and unsolicited verification where the design chose not to
have it, both draw findings. Kani is rejected as disproportionate for
invariants the type system enforces, FFI boundaries, and async I/O;
Verus is expected only once a small, stable pure kernel exists.

## Red flags

- "We already test this" and a one-line mutation does not break the test.
- An `unsafe` block has a safety comment but never runs under Miri.
- A `proptest` regression file is checked in but never minimised or
  promoted to a unit test.
- A Kani harness or Verus proof references symbols that no longer match
  production — the mirror is decaying.
- Concurrency tests pass locally and flake in CI; `loom`, `shuttle`, or
  `turmoil` have not been tried.
- A direct invariant is routed through several selector documents before
  anyone writes the obvious `proptest!` block.
- A `proptest` strategy filters most inputs; construct valid data instead.
- A state-machine test models no history-dependent behaviour.
- A Kani harness has no `#[kani::unwind]` and no CI timeout; bounded
  model checking can run arbitrarily long, so cap the search.
- `cargo-mutants` runs over `cfg(kani)` modules or a slow, flaky
  integration suite; narrow the target.
- A verification CI job runs expensive tools on every push without a
  stated assurance target.
- An `insta` snapshot is treated as the system of record for an
  invariant. The property is the specification; the snapshot is an
  example.

Read
[`references/selection-matrix.md`](references/selection-matrix.md) when
the choice is still unclear, then load the matching deep dive.

## Routing into deep dives

- Strategy design, shrinking discipline, regression files, the
  filtering trap, and state-machine tests:
  [`proptest`](../proptest/SKILL.md).
- Kani harness shape, unwind discipline, contracts, stubbing:
  [`kani`](../kani/SKILL.md).
- Verus modes, triggers, sequence proofs, `assert by`:
  [`verus`](../verus/SKILL.md).

Proptest is a regular Cargo dev-dependency; `kani` and `verus`
install via
[`rust-prover-tools`](https://github.com/leynos/rust-prover-tools).
The selection rules above stay authoritative for picking between
them.

## References

- [`references/selection-matrix.md`](references/selection-matrix.md) —
  at-a-glance comparison, pick-by-question, and common mis-applications.
- [`references/tool-selection.md`](references/tool-selection.md) — per-tool
  "use when" rationale.
- [`references/deterministic-chaos.md`](references/deterministic-chaos.md)
  — determinism fences for chaos tools.
- Deep dives: [`../proptest/SKILL.md`](../proptest/SKILL.md),
  [`../kani/SKILL.md`](../kani/SKILL.md),
  [`../verus/SKILL.md`](../verus/SKILL.md).
