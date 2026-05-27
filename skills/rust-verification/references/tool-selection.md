# Verification tool selection

One paragraph per tool, plus the failure mode each one is best at
detecting. Use alongside the decision table in
[`../SKILL.md`](../SKILL.md).

## Undefined behaviour in `unsafe`

**Miri** is an interpreter for Rust's MIR. It runs each test and reports
undefined behaviour that the optimiser would otherwise hide: invalid
references, uninitialised reads, use-after-free, aliasing violations
under Stacked or Tree Borrows, and incorrect FFI. Reach for Miri
whenever a test exercises an `unsafe` block, a raw-pointer dance, or an
FFI shim. It is slow (tens of times slower than native) but the
diagnostics are precise.

**Sanitizers** (`-Zsanitizer=address`, `=memory`, `=thread`, `=leak`)
catch UB and data races at native speed by instrumenting the compiled
binary. They complement Miri: sanitizers cover more code (including
FFI dependencies) but report less precisely than Miri's abstract
interpretation.

## Input gaps in pure functions

**`proptest`** (and `quickcheck`) generates many random inputs, then
shrinks failing cases to a minimal counter-example. Use it for pure
functions where the input domain is too large to enumerate but a
property (idempotence, round-trip, ordering, conservation) is easy to
express. Always check in the regression file `proptest-regressions/`
and promote shrunk failures to named unit tests.

## "My tests pass but my logic is wrong"

**`cargo-mutants`** rewrites the production code with small mutations
(replace `>` with `>=`, return early, swap arguments) and re-runs the
test suite. A surviving mutant is a hole in the tests. Use it
periodically on the modules that matter; the report tells you which
assertions to strengthen, not which production code to change.

## Async cancellation and partial failure

**`turmoil`** simulates a deterministic distributed environment: nodes,
network partitions, latency, and message drops. It is best for testing
how an async system tolerates timeouts, cancellation, retries, and
peer failure without needing real network conditions. Each scenario
runs end-to-end in a single process.

## Lock-free memory ordering

**`loom`** explores every legal interleaving of atomic operations under
the Rust memory model. Wrap the code in `loom::sync::Arc`,
`loom::sync::atomic::*`, and `loom::thread::spawn`; loom will permute
schedules until a buggy interleaving is found or every reachable
schedule has been explored. Use it for hand-rolled lock-free data
structures and `unsafe` synchronisation primitives.

## Mutex and channel scheduling

**`shuttle`** is loom's cousin for higher-level primitives (`Mutex`,
`RwLock`, `mpsc`). It uses partial-order reduction and random
exploration to find scheduling bugs that classical tests miss. Reach
for it when a bug appears intermittently under contention and is hard
to reproduce.

## Bounded structural invariants

**`kani`** is a bounded model checker. Inputs become symbolic; every
path within stated bounds is explored. It detects panics, out-of-bounds
indexing, integer overflow, and assertion failures. Use it for parsers,
small state machines, and `unsafe` code where the search space is
small enough to bound. Heap collections do not scale; keep harnesses
to a few elements. Load the [`../../kani/SKILL.md`](../../kani/SKILL.md)
skill for harness shape, unwind discipline, and contracts.

## Unbounded algebraic properties

**`verus`** is a deductive verifier built on Z3. It proves properties
of arbitrary size: any-length sequences, all possible orderings, any
number of layers. Specifications are written in `spec`/`proof` modes
and erased at compile time. Use it when a property holds over an
unbounded domain or when a Kani harness keeps growing because the
bounded state space is too large. Load the
[`../../verus/SKILL.md`](../../verus/SKILL.md) skill for spec design,
triggers, and `assert by`.

## Cross-reference

`turmoil`, `loom`, and `shuttle` overlap with the
[`rust-async-and-concurrency`](../../rust-async-and-concurrency/SKILL.md)
skill; the verification skill names them as one tool in a layered
strategy, while the concurrency skill covers the writing style they
expect.
