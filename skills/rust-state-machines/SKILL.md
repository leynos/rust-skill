---
name: rust-state-machines
description: Use for Rust parsers, codecs, protocols, actors, device lifecycles, correlated state fields, transition design, and choosing between runtime algebraic data types (ADTs) and typestate.
globs: ["**/Cargo.toml", "**/*.rs"]
---

# Rust State Machines

Use this when the real question is what the states are, what drives each
transition, and which invalid combinations the representation should exclude.

## Working stance

- Discover semantic states and transitions before choosing Rust syntax.
- Put state-specific data in the variant or type where that data is valid.
- Choose typestate or a runtime ADT according to who selects the transition.
- Give transitions semantic names and semantic result types.
- Encapsulate mandatory setup, cleanup, and finalization in the state owner.
- Keep genuinely independent observations as fields rather than inventing a
  state machine around them.

## Decision surface

| Pressure | Default move |
| --- | --- |
| caller chooses a small, finite operation sequence | typestate or consuming concrete state types |
| parser input, frame, socket, channel, interrupt, or scheduler chooses | runtime enum with state-specific payloads |
| nesting or history is unbounded | runtime ADT plus an explicit stack, queue, or map |
| values live in a homogeneous collection or behind `dyn Trait` | stable owner type with an internal runtime ADT |
| several fields describe one mutually exclusive phase | collapse them into one enum |
| one scalar carries a validated domain invariant | newtype, constructed at the boundary |
| conditions are independent and may coexist | ordinary fields or booleans |

## Representation audit

When a state carrier contains a boolean, `Option`, sentinel integer, empty
collection used as a signal, or fields that must change together, ask whether
those fields disguise a sum type.

Look for:

- matches that reconstruct one logical state from several fields,
- combinations that are representable but treated as impossible,
- `unreachable!()` branches caused by multi-step construction ceremony,
- transitions that mutate several correlated fields and return flags or tuples,
- finalization sequences such as `flush(); into_inner()` or `close(); clear()`,
- typestate variants immediately wrapped in an enum so runtime code can store
  them together.

## Transition design

- Consume `self` when a transition invalidates the previous state.
- Use `&mut self` when the object needs stable identity, but update correlated
  state atomically behind one method.
- Return named transition or outcome enums instead of boolean tuples.
- Use `Result` for technical or unrecoverable failure; use enum variants for
  expected domain alternatives that callers must handle exhaustively.
- Keep pure transition logic separate from I/O where that makes the machine
  easier to test, but do not split one invariant across several owners.

## Verification

- Table-test every legal transition and important rejection.
- Use `trybuild` to prove compile-pass and compile-fail contracts for typestate.
- Use `proptest` for transition sequences, parser inputs, idempotence, and
  round-trips.
- Use Kani for bounded state spaces, ordering, overflow, and reachability
  invariants.
- Test duplicate, cancellation, shutdown, partial-input, and finalization paths,
  not only the happy path.

Read [typestate-vs-runtime-adts.md](references/typestate-vs-runtime-adts.md) for
the central representation choice,
[parsers-protocols-and-gadgets.md](references/parsers-protocols-and-gadgets.md)
for domain patterns, and
[testing-state-machines.md](references/testing-state-machines.md) for a
verification ladder.
