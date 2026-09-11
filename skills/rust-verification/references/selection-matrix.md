# Verification selection matrix

Use this after the testing hierarchy in `rust-router` has ruled out a
named unit test, a finite `rstest` table, and an obvious lightweight
`proptest` property. The matrix chooses an escalation target; it is not
a reason to escalate.

## Enter at the right level

- One exact scenario or finite normative case set → `rust-unit-testing`.
- One relation over many cheap, repeatable inputs → lightweight
  `proptest`.
- Dependent data, operation history, bounded path scrutiny, unbounded
  proof, or suite sensitivity → use the matrix below.

## At a glance

| Concern         | `proptest`                 | `kani`                      |
| --------------- | -------------------------- | --------------------------- |
| Engine          | Generation plus shrinking  | Symbolic execution (CBMC)   |
| Answers         | Does the property survive? | Can a bounded path fail?    |
| Best on         | Data and operation spaces  | Small pure, branchy code    |
| Worst on        | Slow external effects      | Collections, strings, FFI   |
| Typical cadence | Every CI run               | PR smoke tier; nightly full |
| Counter-example | Shrunk small input         | Concrete assignment         |
| Pairs with      | Unit tests, mutants        | proptest, unit-test twins   |

| Concern         | `verus`                   | `cargo-mutants`             |
| --------------- | ------------------------- | --------------------------- |
| Engine          | Deductive proof (Z3)      | Mutation of production code |
| Answers         | Does it hold unbounded?   | Would the suite notice?     |
| Best on         | Pure algebraic kernels    | Fast, stable suites         |
| Worst on        | Collections, bit mixing   | Slow, flaky, `cfg`-gated    |
| Typical cadence | Scheduled or on demand    | Nightly or pre-release      |
| Counter-example | Failed obligation         | Surviving mutant diff       |
| Pairs with      | Kani for the bounded twin | Any existing test style     |

## Pick by question

- "The same relation should hold over many values, and ranges or regex
  literals describe them." → Lightweight `proptest`; no selector ceremony
  is needed.
- "Valid fields depend on one another, data is recursive, or the bug
  needs a sequence of operations." → Advanced `proptest` with
  `prop_compose!`, a derive crate, or `proptest-state-machine`.
- "I want to know whether a small bounded function can reach this failed
  assertion." → `kani` with a tight `#[kani::unwind]`.
- "I refactored a pure kernel and want to know it is equivalent within a
  bound." → `kani` over both versions, or exhaustive unit-test twins.
- "The property has no bound: any length, any ordering." → `verus`, once
  the kernel is small and stable.
- "Tests pass; I do not trust that they would catch a defect." →
  `cargo-mutants`.
- "I have a useful property and want to know whether its assertion is
  sensitive to wrong code." → Combine `proptest` and `cargo-mutants`.
- "The tests already exercise `unsafe`; does it commit UB?" → Miri, then
  sanitizers for foreign code.

## When to leave the cluster

- **Concurrency:** `loom` for atomics on one core, `shuttle` for locks and
  channels, `turmoil` for async partial failure.
- **Performance:** benchmarks and profilers
  (`rust-performance-and-layout`).
- **System invariants:** integration tests with a real or simulated
  database, filesystem, process, or network boundary.
- **Foreign faults:** sanitizers or coverage-guided fuzzers for FFI code.

## Common mis-applications

- Replacing a finite standards table with generated values. The table is
  the specification; keep it readable.
- Building a state machine where a normal `proptest!` already expresses
  the property.
- A `proptest` block driving a real database or process once per case
  without rollback or a tight integration-test budget.
- Kani on heap-heavy or string-heavy code without a kernel extraction and
  a bound; Kani for invariants the type system already enforces; Kani
  across an FFI or async I/O boundary.
- Verus before a pure kernel exists, or over an idealized structure with
  no refinement lemma to the runtime one.
- `cargo-mutants` on a slow or flaky suite, or over `cfg(kani)` modules it
  cannot evaluate, without narrowing the target.
- All of them on every push. Match cadence and cost to the assurance
  question.
