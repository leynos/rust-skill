# Proptest strategy examples

Five worked patterns that come up in almost every property suite:
the round-trip over a composed struct, the filtering-trap fix, the
oracle comparison, a field-dependent strategy via `test-strategy`,
and a `ReferenceStateMachine` sketch. The names are deliberately
generic — adapt them to the production module being tested.

## Round-trip over a composed struct

The default starting shape for a codec or parser test. The strategy
is total (every drawn value is a valid `Order`) and the property is
named for the invariant it checks.

```rust
use proptest::prelude::*;

#[derive(Clone, Debug, PartialEq)]
pub struct Order {
    pub id: u64,
    pub item: String,
    pub qty: u32,
}

prop_compose! {
    fn small_order()(
        id in 1u64..1_000_000,
        item in "[a-z]{3,8}",
        qty in 1u32..1_000,
    ) -> Order {
        Order { id, item, qty }
    }
}

proptest! {
    #[test]
    fn order_codec_roundtrips(order in small_order()) {
        let bytes = encode(&order);
        let decoded = decode(&bytes).expect("our own encoder round-trips");
        prop_assert_eq!(decoded, order);
    }
}
```

The same shape generalizes to:

- `parse(format(x)) == x` for a printer/parser pair,
- `sort(sort(xs)) == sort(xs)` for idempotence,
- `len(map(f, xs)) == len(xs)` for length preservation.

## The filtering trap: before and after

Filtering invalid inputs out hurts both runtime (rejection budget)
and shrinking (the runner cannot tell rejection from success).
Construct only valid values from the seed instead.

Before — `prop_filter` throws away half the cases and confuses the
shrinker:

```rust
proptest! {
    #[test]
    fn even_is_even(
        n in any::<u32>().prop_filter("must be even", |n| n % 2 == 0)
    ) {
        prop_assert_eq!(n % 2, 0);
    }
}
```

After — every drawn value is even by construction:

```rust
prop_compose! {
    fn even_u32()(half in any::<u32>()) -> u32 { half.wrapping_mul(2) }
}

proptest! {
    #[test]
    fn even_is_even(n in even_u32()) {
        prop_assert_eq!(n % 2, 0);
    }
}
```

The same recipe fixes "a less than b":

```rust
// Before (rejection-heavy):
//   any::<u32>().prop_flat_map(|b| (0..=b, Just(b)))  // OK, no filter
// or:
//   (any::<u32>(), any::<u32>())
//       .prop_filter("a<b", |(a,b)| a < b)            // bad

prop_compose! {
    fn ordered_pair()(b in 1u32..)(a in 0u32..b, b in Just(b)) -> (u32, u32) {
        (a, b)
    }
}
```

Note the second `Just(b)` — `prop_compose!` rebinds `b` in the
second clause from the strategy expression, so it has to be passed
through explicitly.

## Oracle comparison against a reference implementation

When a slow, obviously-correct reference implementation exists, the
property is "the production function agrees with the reference".

```rust
fn slow_sum(xs: &[u64]) -> u128 {
    xs.iter().map(|x| *x as u128).sum()
}

proptest! {
    #[test]
    fn fast_sum_matches_oracle(
        xs in prop::collection::vec(any::<u64>(), 0..256),
    ) {
        prop_assert_eq!(fast_sum(&xs), slow_sum(&xs));
    }
}
```

The reference must be structurally different from the production
code. A reference that quietly calls the production function
proves only that copy-paste works.

## Field-dependent strategies with `test-strategy`

`prop_compose!` cannot express "field `b` depends on field `a`"
without a manual `prop_flat_map`. `test-strategy` adds a `#[strategy(...)]`
attribute that can reference earlier fields with `#name`:

```rust
use test_strategy::Arbitrary;

#[derive(Arbitrary, Debug)]
struct WindowedRange {
    #[strategy(1u32..1_000)]
    width: u32,

    // `start` is constrained to `0..=u32::MAX - width` so
    // `start + width` cannot overflow.
    #[strategy(0..=u32::MAX - #width)]
    start: u32,
}
```

The `#[proptest]` attribute on a test function pairs naturally with
this derive and preserves normal `rustfmt` formatting:

```rust
use test_strategy::proptest;

#[proptest]
fn window_never_overflows(input: WindowedRange) {
    let _end = input.start.checked_add(input.width).expect("no overflow");
}
```

## State-machine sketch

`proptest-state-machine` generates sequences of transitions and
shrinks failing sequences to the shortest reproducer. The pattern is
two trait impls: `ReferenceStateMachine` models the abstract
expected behaviour; `StateMachineTest` drives the real system and
checks invariants after each step.

```rust
use proptest::prelude::*;
use proptest_state_machine::{ReferenceStateMachine, StateMachineTest};

#[derive(Clone, Debug)]
enum Op { Inc, Dec }

struct Counter;

impl ReferenceStateMachine for Counter {
    type State = i32;
    type Transition = Op;

    fn init_state() -> BoxedStrategy<Self::State> {
        Just(0).boxed()
    }

    fn transitions(_: &Self::State) -> BoxedStrategy<Self::Transition> {
        prop_oneof![Just(Op::Inc), Just(Op::Dec)].boxed()
    }

    fn apply(state: Self::State, op: &Self::Transition) -> Self::State {
        match op { Op::Inc => state + 1, Op::Dec => state - 1 }
    }
}

struct CounterSut(MyCounter);

impl StateMachineTest for CounterSut {
    type SystemUnderTest = MyCounter;
    type Reference = Counter;

    fn init_test(_ref_state: &i32) -> Self::SystemUnderTest {
        MyCounter::new()
    }

    fn apply(
        mut sut: Self::SystemUnderTest,
        ref_state: &i32,
        op: Op,
    ) -> Self::SystemUnderTest {
        match op { Op::Inc => sut.inc(), Op::Dec => sut.dec() }
        // Invariant check after each transition.
        assert_eq!(sut.value(), *ref_state, "SUT diverged from reference");
        sut
    }
}

prop_state_machine! {
    #[test]
    fn counter_matches_reference(sequential 1..100 => CounterSut);
}
```

The `prop_state_machine!` macro generates a property that draws a
sequence of length 1..100, applies it to both the reference state
and the system under test, and shrinks any divergence to the
smallest failing trace. State-machine tests pay back the
investment on collections, caches, allocators, and protocol
clients where the bug needs a particular history to surface.

## Cross-references

- [`SKILL.md`](../SKILL.md) for the working stance, anti-patterns,
  and configuration knobs.
- [`installation-note.md`](installation-note.md) for the dependency
  matrix and environment variables.
- [`proptest-example.rs`](proptest-example.rs) for a self-contained
  Rust source illustrating the file layout.
