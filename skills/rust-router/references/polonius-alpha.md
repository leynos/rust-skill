# Polonius Alpha project posture

Polonius Alpha is a compiler capability that changes which sound borrowing
forms are accepted. It is not a separate Rust dialect and should not create
parallel Polonius editions of the ordinary language skills.

As of 4 August 2026, current Rust nightly enables Polonius Alpha by default
while the Rust project prepares it for stabilization. Nightly users can opt
back into NLL with `-Zpolonius=off`. The explicit
`-Zpolonius=next` spelling still selects the Alpha implementation and remains
useful for older pinned nightlies or deliberate comparison, but current
nightly projects do not need to add it mechanically.

## Determine the project posture

Use the first decisive signal and record one of four values:
`polonius-alpha`, `nll`, `polonius-legacy`, or `unknown`.

1. Inspect `rust-toolchain.toml`, `rust-toolchain`, `.cargo/config.toml`,
   `.cargo/config`, CI commands, compiler wrappers, `RUSTFLAGS`, and
   `CARGO_ENCODED_RUSTFLAGS`.
2. Explicit checker selection wins:
   - `-Zpolonius=next` means `polonius-alpha`;
   - `-Zpolonius=off` means `nll`;
   - `-Zpolonius=legacy` means `polonius-legacy`.
3. A current unmodified nightly means `polonius-alpha`.
4. A dated nightly may predate the default. A stable compiler may eventually
   include Alpha after stabilization. When the version or wrapper leaves any
   doubt, compile the canary rather than encoding a date table in the skill.

Use the compiler selected by the project, not whichever `rustc` happens to be
first on `PATH`:

```rust
fn reborrow(a: &mut u8) -> &mut u8 {
    let b = &mut *a;
    if true { b } else { a }
}
```

The canary is accepted by Polonius Alpha and rejected by NLL. For a current
nightly, an NLL control run can be made explicit:

```bash
rustc --crate-type=lib polonius_canary.rs
rustc -Zpolonius=off --crate-type=lib polonius_canary.rs
```

If execution is unavailable, keep the posture `unknown` and make any
borrow-sensitive recommendation conditional. Do not infer Alpha merely from a
comment or from the presence of an NLL-shaped workaround.

## What Alpha changes

Polonius Alpha makes lifetime outlives relationships flow-sensitive. The most
important newly accepted shapes are:

- NLL problem case 3: return a borrow on one control-flow path, then reborrow
  or mutate on a path where that loan did not escape;
- lending-iterator filters and related conditional escapes from a loop;
- get-or-insert, scan-then-mutate, and lazy-error-context APIs whose direct
  borrowing form was rejected because NLL kept a loan live on the wrong path.

When Alpha is active, try the natural borrowing form before accepting a clone,
double lookup, index/id indirection, eager error construction, or interior
mutability whose only purpose is to placate NLL. Compile the candidate with the
project's configured compiler. The compiler is the oracle at the edge of the
Alpha analysis.

## What Alpha does not change

Polonius Alpha does not relax mutation-xor-sharing or make simultaneous
aliasing sound. It also does not remove:

- ownership requirements across `.await`, task, thread, channel, callback,
  event-loop, process, or serialization boundaries;
- `Send` and `Sync` requirements;
- self-reference and struct-field lifetime constraints;
- full flow-sensitivity for every loop-carried conditional reborrow;
- the need to measure runtime effects of any clone-removal or API rewrite.

The old datalog implementation selected by `-Zpolonius=legacy` accepts some
more exotic patterns but is not the stabilization target. Treat a project that
uses it as a migration case and load `nll-to-polonius`.

## How ordinary skills consume the posture

- `rust-memory-and-state`: under `polonius-alpha`, test the direct borrow-flow
  design before clones, repeated lookups, ids, or interior mutability; still
  refuse genuine simultaneous aliasing.
- `rust-async-and-concurrency`: use Alpha for local control-flow borrowing, but
  keep suspension-point, task, and thread ownership explicit.
- `rust-performance-and-layout`: revisit clone-heavy or snapshot-heavy hot
  paths that may be NLL residue, then benchmark the resulting design. The
  checker itself changes compile-time analysis, not runtime semantics.

Load `nll-to-polonius` only when adopting Alpha, auditing NLL residue, or
evolving APIs is itself the task. Merely working in an Alpha-enabled project
does not justify replacing the normal skill route.

## Primary sources

- [Enabling the next iteration of the borrow checker on nightly](https://blog.rust-lang.org/2026/08/04/enabling-polonius-alpha-on-nighty/)
- [2026 goal: Stabilize and model Polonius Alpha](https://rust-lang.github.io/goals/2026/polonius.html)
