# Bounding harnesses and containing resource growth

A Kani harness has no memory budget of its own. CBMC keeps allocating until it
finishes or the operating system stops it. On a developer machine that is an
annoyance. On a shared host or a CI runner it starves every neighbouring
process long before anything is killed for running out of memory. Treat the
bounds as a resource budget that you choose, measure, and record. They are not
a dial to turn up until the proof passes.

## Where the cost comes from

- **Symbolic width.** Every byte from `kani::any()` multiplies the input space
  by 256. CBMC does not enumerate that space, but each branch on symbolic data
  that it cannot merge splits symbolic execution. The cost of a harness often
  grows exponentially in the number of symbolic bytes, not linearly.
- **Unwind depth.** `#[kani::unwind(n)]` applies to *every* loop the harness
  reaches, including loops inside `core` and `alloc` (`run_utf8_validation`,
  `Vec` growth, `String` pushes, iterator adaptors). A bound sized for your own
  loop is also the bound for every library loop under it.
- **Width times depth.** A library loop that iterates once per symbolic byte,
  unwound to a generous bound, inside code that branches on those bytes, is the
  usual recipe for a runaway. Each extra byte of width or level of depth
  multiplies the other's cost.
- **Heap models.** `Vec`, `String`, `Box`, and the allocator are modelled
  explicitly. Allocating a buffer whose length depends on symbolic data, and
  then growing it, costs far more than working on a fixed array or a borrowed
  slice.

## Choosing bounds

1. **Start at the smallest bound that can reach the property.** Derive it from
   the claim, for example "every retained-tail length up to three needs three
   input bytes", and write that reasoning in the harness's doc comment next to
   the numbers.
2. **Let the unwinding check tell you when the bound is too small.** Kani's
   unwinding assertions are on by default. A bound one short of a loop's real
   trip count fails with an `unwinding assertion loop N` violation, naming the
   loop. Raise the bound one step at a time in response to that failure. Never
   pre-emptively round up to a "safe" value. Never pass `--no-unwinding-checks`
   to make a bound fit, because it turns the bound into a silent truncation and
   the proof into a claim about a prefix.
3. **Grow symbolic width one step at a time, measuring at each step.** Run
   N, then N+1, and record peak memory and wall time for both. Two points show
   whether growth is linear or a cliff. Stop at the first width that proves the
   claim; cover the next length with a concrete harness (a fixed four-byte
   input, for example) rather than a symbolic one.
4. **Prefer the harness attribute to the command line.** `--unwind` overrides
   `#[kani::unwind]` for the harness it selects, and `--default-unwind` applies
   to every harness without an attribute. A raised command-line bound in a
   Makefile or an ad hoc rerun silently replaces the reviewed bound in the
   source.
5. **Keep library internals out of the symbolic path where you can.** Push
   `core`/`alloc` calls onto concrete data. Assume the library's postcondition
   (`kani::assume` on the result) when the library function is not what you are
   proving. Stub it with `#[kani::stub]`. Or extract a kernel that works on a
   fixed array or slice so that no `Vec`/`String` is built from symbolic
   lengths.
6. **Split, don't widen.** Two harnesses at width three with different
   preconditions are usually far cheaper than one at width four. Partition by
   the branch that matters (valid prefix versus malformed lead byte) using
   `kani::assume` at each harness's call site, and add a `kani::cover!` to each
   so that neither partition is vacuous.

## Running a harness under a budget

Iterate on one harness at a time, by exact name, and never under a whole-crate
run:

```bash
cargo kani --package my-crate --harness utf8::kani_proofs::pending_tail --exact
```

Put a ceiling on memory and wall time for every exploratory run. A memory cap
turns a runaway into a prompt, attributable failure instead of host-wide
starvation:

```bash
# Preferred on systemd hosts: a transient cgroup with a hard memory ceiling
# and no swap, so the run fails fast instead of thrashing.
systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 -- \
  timeout --kill-after=30s 20m \
  /usr/bin/time -v \
  cargo kani --package my-crate --harness NAME --exact
```

- `timeout --kill-after` matters: CBMC installs a `SIGTERM` handler and has
  been observed to keep solving after receiving one. Plain `timeout` (which
  sends `SIGTERM`) may not stop it; escalate to `SIGKILL`.
- `/usr/bin/time -v` reports `Maximum resident set size` for the largest
  child, which is the CBMC process. Record that figure, not the wall time alone.
- Without systemd, `prlimit --as=<bytes>` or `ulimit -v` caps virtual address
  space instead. That is a cruder limit, and it also applies to the compilation
  step, so set it well above the compiler's needs.
- Kani's own `--harness-timeout` (requires `-Z unstable-options`) bounds each
  harness's wall time. It does not bound memory.
- Run harnesses sequentially. `-j` multiplies peak memory by the number of
  harnesses solving at once.

## Recognising a runaway early

With Kani's default `regular` output, CBMC reports its phases per harness. A
healthy harness passes through them quickly:

```text
Runtime Symex: 0.11s
size of program expression: 2548 steps
Generated 219 VCC(s), 34 remaining after simplification
Running propositional reduction
Solving with CaDiCaL 2.0.0
238722 variables, 650571 clauses
```

Warning signs, in the order they usually appear:

- **No `size of program expression` line after a minute or two.** Symbolic
  execution has not finished building the formula. This is where memory grows
  without bound, and it is the phase a runaway is most often stuck in.
- **A flood of `Not unwinding loop … iteration N` lines for the same loop.**
  Many symbolic paths are reaching the unwind bound of one loop. That loop, and
  usually a library loop, is where width and depth are multiplying.
- **Program-expression steps or clause counts growing by an order of magnitude
  between N and N+1.** You have found the cliff; do not take the next step.

Stop the run at the first sign, not after it has consumed the machine.

## Things never to do

- **Do not evade a limit that stopped a proof.** If a harness is killed by a
  timeout, a memory cap, an agent harness's background-task limit, or an
  operator, the kill is information about the harness. Do not rerun it detached
  (`setsid`, `nohup`, `disown`, a fresh terminal) or outside its cgroup to let
  it "finish". Find which harness grew, bound it, and rerun that harness alone
  under a cap.
- **Do not rerun the whole crate or the full gate to test a rebound harness.**
  Prove the one harness under a cap first; only then run the gate.
- **Do not raise a bound in the gate's command line to make a harness pass.**
  Change the attribute, justify the number in the doc comment, and update the
  harness inventory.

## Recording the budget

Add peak resident memory and wall time to each harness's row in the harness
inventory alongside its bounds. A reviewer can then see that width three costs
about 15 s and stays small, and that width four was measured and abandoned. A
future refactor that pushes a harness from seconds to minutes then shows up as
a diff to a recorded number rather than as a stalled CI job.

## Case study: a symbolic UTF-8 tail

`cuprum`'s `pending_tail_stays_bounded_for_symbolic_input` decoded a symbolic
byte array through production code that builds a `Vec<u8>` and a `String` and
calls `core::str::from_utf8`. The gate ran it with `--unwind 8` over four
symbolic bytes. CBMC never left symbolic execution. Its log repeated
`Not unwinding loop … run_utf8_validation … iteration 8`, and after nearly two
hours it held 56 GiB resident on a shared host and throttled every other agent
in its cgroup. `SIGTERM` did not stop it; `SIGKILL` did. The session that
started it read the kill as a tooling limit and relaunched the gate detached,
reproducing the growth until an operator intervened.

The bounded version uses three symbolic bytes, which still reach every
retained-tail length the decoder permits, with an unwind bound of five. The
reasoning is written in the doc comment. It sits beside fixed four-byte
harnesses that cover the longest payload concretely. Its sibling harnesses at
the same width solve in about 15 s.
