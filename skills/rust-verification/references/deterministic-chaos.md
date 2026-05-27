# Deterministic chaos: keeping verification reproducible

`loom`, `shuttle`, `turmoil`, and `kani` need the system under test to
be deterministic given its inputs. Otherwise a discovered counter-example
cannot be replayed, the search loops, or the verifier reports false
negatives because the same inputs produced different outputs on
different schedules. The cure is a thin layer of inversion of control.

## What breaks determinism

- **Wall-clock time** (`std::time::Instant::now`, `SystemTime::now`):
  introduces non-reproducible ordering and timeouts.
- **Random number generators** seeded from the OS: every run picks a
  different code path.
- **Thread-local IDs and addresses**: pointer values, `ThreadId`, and
  default `HashMap` hash seeds vary across runs and across `loom`
  iterations.
- **Environment reads** (`std::env::var`, file-system layout): the
  verifier cannot replay them.
- **Network I/O** in async code: even when the tool intercepts it
  (`turmoil`), the production code must not bypass the abstraction.

## Pattern: inject the source of non-determinism

Wrap each source in a trait or function pointer; let the production
build use the real source and the verification build inject a
deterministic stub.

```rust
pub trait Clock {
    fn now(&self) -> Instant;
}

pub trait RandomBits {
    fn next_u64(&mut self) -> u64;
}

// Production: SystemClock { ... }, OsRng { ... }
// Tests:      FakeClock { tick: Cell<u64> }, SeededRng { ... }
```

The same pattern works for environment lookups, peer discovery, and
filesystem paths. Once injected, `loom`, `shuttle`, and `turmoil` can
drive the system through every interesting interleaving without the
underlying source drifting.

## Pattern: avoid pointer-identity comparisons in invariants

`Arc::ptr_eq`, `*const T` equality, and `HashMap` ordering all depend
on values that vary between `loom` schedules. Substitute logical
identifiers (`NodeId`, `EpochId`, `RequestId`) before asserting an
invariant.

## Pattern: keep timeouts virtual

In `turmoil`, use the simulated clock rather than `tokio::time::sleep`
in production code. In `loom` and `shuttle`, replace timed waits with
condvars or channels — the schedulers cannot model real time, only the
order of operations.

## Pattern: cap the search before celebrating

A `loom` or `shuttle` run that completes quickly is suspicious: the
state space may have been pruned by an early `return`, a never-taken
branch, or a deterministic value that should have been symbolic. Print
the number of explored interleavings and the iteration cap; raise the
cap and re-run before declaring success.

## Pattern: bridge to symbolic checkers

Kani harnesses need `kani::any::<T>()` everywhere a real run would draw
from a non-deterministic source. Reuse the trait abstraction above: the
Kani-only `Clock` and `RandomBits` implementations call `kani::any()`,
and the harness drives the same production code that runs under `loom`
and `shuttle`.

## Anti-pattern: gating chaos behind `#[cfg(test)]` only

Verification tools often need their own cfg (`#[cfg(loom)]`,
`#[cfg(kani)]`, `#[cfg(shuttle)]`) because they cannot be enabled
simultaneously with each other or with regular tests. Declare each cfg
in `Cargo.toml` so unused-cfg warnings do not mask drift:

```toml
[lints.rust]
unexpected_cfgs = { level = "warn", check-cfg = [
    "cfg(loom)", "cfg(shuttle)", "cfg(kani)",
] }
```

## Cross-reference

The injection pattern aligns with
[`rust-async-and-concurrency`](../../rust-async-and-concurrency/SKILL.md)'s
treatment of cancellation and shutdown. When the trait surface starts
to feel like a runtime abstraction, that is the right time to consult
[`arch-crate-design`](../../arch-crate-design/SKILL.md) on where to
place it.
