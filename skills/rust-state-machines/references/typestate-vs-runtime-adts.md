# Typestate versus Runtime ADTs

The first question is not whether Rust can encode a transition in a type. It
is who knows the next state when the code is compiled.

## Choose typestate for caller-driven protocols

Typestate fits when the caller deliberately selects a small, finite sequence
of operations:

```text
Unbound -> Bound -> Running
Draft -> Sealed -> Sent
OpenTransaction -> Committed | RolledBack
```

Represent each state with a concrete type or a marker parameter. Put methods
only on states where they are legal, consume `self` when the previous state
must not be reused, and return the next state.

Prefer separate concrete types when the states have substantially different
data or APIs. Prefer `Thing<State>` when they share meaningful representation
or behaviour and the generic parameter remains simple.

Typestate earns its boilerplate when an out-of-order call would corrupt data,
leak a resource, violate a protocol, or otherwise fail too late at runtime.
It earns less in a long but mostly linear pipeline where each state exists only
to name the next function call.

## Choose a runtime ADT for event-driven machines

A parser token, network frame, socket readiness event, channel closure,
interrupt, timer, or scheduler decision is known only at runtime. Keep one
stable owner type and put the current state in an enum:

```rust
struct Decoder {
    state: DecodeState,
}

enum DecodeState {
    Header,
    Payload { expected: usize, buf: Vec<u8> },
    Complete { frame: Frame },
}
```

This also fits machines stored in a homogeneous collection, shared behind a
trait object, polled through `Stream`, or retained across an actor loop. Those
interfaces require one stable concrete type while logical state changes.

If generic typestates must immediately be wrapped in an enum so runtime code
can store or branch over them, the enum is usually the useful abstraction.
Remove the inner type-level theatre unless it still prevents misuse at a
caller-controlled boundary.

## Hybrid machines are normal

A system may use both representations at different layers. For example:

- a builder uses typestate to require configuration before `start()`,
- the running service uses a runtime ADT for socket and shutdown events;
- a device handle uses typestate for `Disabled -> Configured -> Enabled`,
- its interrupt handler uses a runtime ADT for transfer progress.

Do not force one representation across the whole system. Encode each boundary
according to who controls it.

## Preserve state-specific data

The strongest runtime ADTs do more than replace a flag with a named enum. They
move data into the state where that data is valid:

```rust
// Weak: `buf` and `depth` must agree with `inside`.
struct Scanner {
    inside: bool,
    buf: Vec<String>,
    depth: usize,
}

// Strong: outside state cannot carry an interior buffer or depth.
enum Scanner {
    Outside,
    Inside {
        buf: Vec<String>,
        depth: std::num::NonZeroUsize,
    },
}
```

Apply the same test to typestate. A state type should carry the data produced
and required by that phase, rather than merely decorating unchanged storage
with `PhantomData`.

## Resist enum inflation

A boolean is correct when it records one independent fact. Several booleans
are also correct when every combination is meaningful and may coexist, such
as independent readiness guards in a `select!` loop.

Introduce an ADT when it removes impossible combinations, associates payloads
with valid states, or forces exhaustive handling of real alternatives. Do not
replace `has_cheese: bool` with `CheesePresence::{Present, Absent}` merely to
banish the word `bool`.

## Litmus tests

Ask:

1. Can the caller know and choose the next operation statically?
2. Does consuming the old state prevent a real misuse?
3. Must values in different states share one collection, trait object, or poll
   interface?
4. Does input or an external event choose the transition?
5. Can an enum put each payload only in the state where it is valid?
6. Would typestate add several types without making any invalid call fail to
   compile?

Answers 1 and 2 favour typestate. Answers 3 to 5 favour a runtime ADT. A yes to
6 is the type system asking you to put the marker structs back in the drawer.

## Evidence and restraint

The 2026 FUNARCH experience report *Functional State Machines in Rust:
Typestate and Newtype Patterns* found improved testability and faultlessness
from typestate, but contested readability and added boilerplate. Its authors
suggest that complex branching and interacting invariants benefit more than a
predominantly linear flow. Treat that as a reason to choose typestate
selectively, not as a mandate to encode every workflow in types.
