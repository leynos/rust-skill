# Parsers, Protocols, and Gadgets

These domains often contain several state machines at once. Separate them by
transition driver and ownership boundary instead of forcing one grand machine
through every layer.

## Parsers and codecs

Input chooses parser transitions, so use a runtime ADT. Put partial data in the
state that owns it:

```rust
enum ParseState {
    Start,
    InHeader { fields: HeaderFields },
    InBody { header: Header, buf: Vec<u8> },
    Complete { message: Message },
}
```

For nested or recursively structured input, an enum alone is not enough. Add an
explicit stack, queue, arena, or map whose size is determined at runtime. Do not
attempt to express arbitrary nesting depth through recursive typestate
parameters.

Useful parser smells include:

- `inside: bool` beside a buffer that is meaningful only inside,
- `expected: Option<usize>` where `None` means "reading the header",
- an empty vector or zero integer used as a phase marker,
- several booleans reconstructed into one transition on every token,
- a required `flush()` before extracting output.

Expose a consuming `finish(self)` when end-of-input must flush pending state or
validate that no partial construct remains. Make incomplete-input failure a
semantic error, not a forgotten call-site ritual.

## Framing, reassembly, and wire protocols

Protocol engines usually keep one stable owner while frames drive logical
state. Runtime ADTs work well for:

- connection lifecycle,
- frame decoding,
- fragmented-message assembly,
- sequence tracking,
- request/response output modes,
- graceful shutdown and cancellation.

Model progress directly:

```rust
enum SequenceProgress {
    NotTracking,
    Tracking { next: SequenceNumber },
    Complete { last: SequenceNumber },
}
```

This is stronger than `tracking: bool`, `next: Option<_>`, and
`complete: bool`. Each variant carries exactly the data its transition needs.

Keep protocol errors and expected outcomes distinct. A malformed frame or I/O
failure belongs in `Result`; an accepted fragment that leaves a message
incomplete is an expected state transition. Return a named transition enum when
callers must distinguish such outcomes exhaustively.

Avoid constructors that require immediate follow-up ceremony:

```rust
let mut series = FragmentSeries::new(id);
let status = series.accept(first)?;
```

Prefer a constructor or starting transition that validates the first frame and
returns `Complete` or `InProgress(FragmentSeries)` directly. This removes
branches that callers can only mark `unreachable!()`.

When a protocol implementation lives behind `dyn Trait`, in a `HashMap`, or
inside a `Stream`, generic typestate cannot change the stored concrete type.
Use an internal runtime ADT. Reserve typestate for the external API boundary
where a caller chooses operations such as `bind()`, `authenticate()`, or
`start()`.

## Actors and asynchronous services

An actor loop often combines several independent conditions with one logical
lifecycle. Keep those concepts separate:

```rust
enum Lifecycle {
    Running,
    Draining,
    Finished,
}

struct Readiness {
    input: bool,
    output: bool,
    timer: bool,
}
```

The lifecycle is mutually exclusive and wants an enum. Readiness flags may be
independent and therefore remain booleans. Encoding every readiness subset as a
variant creates a combinatorial catalogue of states without removing invalid
combinations.

Shutdown results should describe what happened, not expose correlated flags:

```rust
enum ShutdownOutcome {
    AlreadyIdle,
    ResponseClosed,
    StreamClosed { correlation_id: Option<u64> },
}
```

This is preferable to a struct containing `source_closed`,
`call_on_command_end`, and an optional identifier whose valid combinations are
known only by convention.

## Devices and gadgets

Hardware APIs commonly contain a useful hybrid:

```text
Caller-controlled lifecycle:
Unconfigured -> Configured -> Enabled

Runtime transfer lifecycle:
Idle -> Receiving -> Complete | Fault
```

Typestate may prevent callers from reading before configuration, transmitting
while disabled, or reusing a consumed one-shot capability. Interrupts, DMA
completion, link changes, and device faults remain runtime events and belong in
an enum inside the stable handle or driver task.

Treat ownership of a peripheral, DMA buffer, permit, lock, or file descriptor
as part of the state. A transition that invalidates the old capability should
consume it. A background event that updates a long-lived driver should mutate
one encapsulated runtime state atomically.

Do not put `Drop` on a type merely to launch asynchronous cleanup. Rust cannot
await in `Drop`. Provide an explicit awaited finalizer where the protocol
requires one, and use RAII only for synchronous cleanup or as a backstop whose
limitations are documented.

## Transition ownership

The type that owns the invariant should own the transition. Prefer:

```rust
let output = buffer.finish()?;
```

over:

```rust
buffer.flush()?;
let output = buffer.into_output();
```

Prefer:

```rust
let outcome = active_output.shutdown();
```

over taking a pre-transition snapshot, clearing several fields, and asking the
caller to infer which hooks and terminators remain owed.

A good transition method leaves one valid state behind, or consumes the owner
and returns another valid state. It should not require callers to remember a
second mutation that restores the invariant.
