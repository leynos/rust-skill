# Newtypes and Typestate

Use a newtype when two values share a representation but not a meaning.

```rust
struct UserId(u64);
struct OrderId(u64);
```

Use typestate at an API boundary when a caller-selected operation order matters
and a state transition is the point:

```rust
struct Draft;
struct Sent;
struct Message<State> { state: State }
```

Do not use typestate just to look clever. If the state machine is open-ended,
data-driven, or mostly runtime, an enum is usually cleaner. Load
`rust-state-machines` when the main question is the state model, transition
driver, or choice between typestate and a runtime ADT.
