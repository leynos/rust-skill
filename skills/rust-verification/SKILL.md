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

- [`references/tool-selection.md`](references/tool-selection.md) — per-tool
  "use when" rationale.
- [`references/deterministic-chaos.md`](references/deterministic-chaos.md)
  — determinism fences for chaos tools.
- Deep dives: [`../proptest/SKILL.md`](../proptest/SKILL.md),
  [`../kani/SKILL.md`](../kani/SKILL.md),
  [`../verus/SKILL.md`](../verus/SKILL.md).
