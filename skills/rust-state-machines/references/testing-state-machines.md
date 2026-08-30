# Testing State Machines

State-machine tests should validate the transition system and its invariants,
not merely replay three attractive examples.

## Start with a transition table

Write down each state, input, result, next state, and side effect. Turn the
important rows into parameterized tests:

| State | Input | Outcome | Next state |
| --- | --- | --- | --- |
| idle | first fragment | accepted | assembling |
| assembling | next fragment | accepted | assembling |
| assembling | final fragment | complete | complete |
| complete | duplicate final fragment | duplicate | complete |
| complete | new fragment | rejected | complete |

Include rejection paths. A machine tested only through legal happy paths says
nothing about the invalid transitions its representation or methods claim to
prevent.

## State invariants

Assert properties that must hold after every transition, for example:

- a completed series cannot accept new progress,
- tracked sequence state always carries the next expected number,
- an outside parser state owns no interior buffer,
- buffered byte counts never exceed declared limits,
- finalization emits at most one terminator,
- shutdown and cancellation are idempotent where promised,
- each acquired resource is released exactly once,
- errors leave the owner in a documented valid state.

Keep invariant checks close to the test model. Do not expose production fields
solely so tests can poke at an invalid representation.

## Typestate contracts

Use ordinary tests for transition behaviour and `trybuild` for API legality.
Provide compile-pass cases for intended sequences and compile-fail cases for
operations such as:

- sending before binding or authentication,
- using a consumed state twice,
- committing after rollback,
- extracting output before finalization.

Compile-fail tests are valuable only when the compile error is part of the
contract. Do not snapshot enormous, unstable diagnostics when a narrower
public-boundary assertion will do.

## Property and model-based tests

Use `proptest` when sequences or inputs matter more than individual examples.
A useful pattern is a small reference model plus generated commands:

1. Generate a bounded sequence of commands or tokens.
2. Apply each command to the model and implementation.
3. Compare outcomes and externally visible state.
4. Assert invariants after every step, not only at the end.
5. Let shrinking find the shortest failing transition sequence.

Good properties include:

- encode/decode and parse/print round-trips,
- repeated finalization or shutdown is harmless or consistently rejected,
- duplicate frames do not duplicate output,
- accepted bytes equal emitted bytes plus buffered bytes,
- sequence numbers advance monotonically until completion,
- no command sequence reaches an impossible state.

Avoid excessive `prop_filter`; generate legal commands from the model's current
state, or deliberately generate both legal and illegal commands and classify
the expected result.

## Bounded model checking

Use Kani when the state space and input alphabet can be bounded tightly. It is
well suited to:

- integer overflow at sequence boundaries,
- all transition sequences up to a small depth,
- reachability of forbidden variants,
- duplicate and reordering behaviour,
- conservation properties over small buffers,
- cleanup flags and exactly-once finalization.

State the unwind bound deliberately. A successful harness that silently stops
before the longest meaningful transition path proves less than it appears to.

## Concurrency and event order

For actors, sockets, channels, and shutdown logic, vary event order explicitly.
Test:

- input and cancellation becoming ready together,
- output closure during draining,
- producer disappearance with buffered work outstanding,
- repeated close notifications,
- cancellation before setup completes,
- cancellation after setup when teardown is still owed.

Use `loom`, `shuttle`, or `turmoil` when the defect depends on task scheduling,
memory ordering, or simulated network behaviour. Keep deterministic model
state separate from the executor or transport harness so failures can shrink or
replay.

## Fault injection

Inject failures at every transition that performs I/O or allocation with a
meaningful recovery contract. Check both the returned error and the surviving
state. In particular, verify whether callers may retry, must discard the owner,
or still owe cleanup.

A transition that can fail halfway through should either:

- perform all validation before mutation,
- build the next state separately and commit it atomically,
- or document and test the recoverable intermediate state.

"The next call repairs it" is not an invariant.

## Coverage discipline

Combine techniques rather than asking one tool to carry the whole machine:

- table tests document named transitions,
- `trybuild` checks typestate call-order contracts,
- `proptest` explores long input and command sequences,
- Kani exhausts small bounded spaces,
- concurrency tools vary schedules and event order,
- end-to-end tests verify wire, file, or device-visible behaviour.

The smallest useful test is the one that fails for the broken invariant and
stays stable when unrelated implementation details change.
