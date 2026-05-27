//! Proptest file-layout reference.
//!
//! Demonstrates the everyday shape of a proptest module: imports,
//! a `prop_compose!` strategy, a `proptest!` block with a round-trip
//! property, a configuration override, and a promoted regression
//! test. Included for reference only; the file is not compiled by
//! `rustc`.
//!
//! Pairs with `skills/proptest/SKILL.md` and
//! `skills/proptest/references/strategy-examples.md`.

// ---------------------------------------------------------------------------
// Cargo.toml: dev-dependency layout
// ---------------------------------------------------------------------------
//
// [dev-dependencies]
// proptest = "1"
// # Optional: derive the default Arbitrary on user types.
// proptest-derive = "0.5"

// ---------------------------------------------------------------------------
// Module placement: a tests submodule co-located with production code
// ---------------------------------------------------------------------------
//
// In src/order.rs:
//
// #[cfg(test)]
// mod proptests {
//     use super::*;
//     // ... contents of this file ...
// }
//
// Regression files land in `proptest-regressions/order.txt` (the
// SourceParallel default) and must be committed alongside the test.

// ---------------------------------------------------------------------------
// Imports and types under test
// ---------------------------------------------------------------------------

use proptest::prelude::*;

#[derive(Clone, Debug, PartialEq)]
pub struct Order {
    pub id: u64,
    pub item: String,
    pub qty: u32,
}

pub fn encode(order: &Order) -> Vec<u8> { /* production code */ Vec::new() }

pub fn decode(bytes: &[u8]) -> Result<Order, DecodeError> {
    /* production code */
    Err(DecodeError)
}

#[derive(Debug)]
pub struct DecodeError;

// ---------------------------------------------------------------------------
// Strategy: a total generator for the type under test
// ---------------------------------------------------------------------------
//
// Every drawn value is a valid Order. There is no prop_filter or
// prop_assume! anywhere; the strategy is the source of validity.

prop_compose! {
    fn small_order()(
        id in 1u64..1_000_000,
        item in "[a-z]{3,8}",
        qty in 1u32..1_000,
    ) -> Order {
        Order { id, item, qty }
    }
}

// ---------------------------------------------------------------------------
// Property: round-trip the codec
// ---------------------------------------------------------------------------

proptest! {
    // Tighter envelope for nightly: 10x more cases, fork+timeout so a
    // pathological input cannot hang the whole suite.
    #![proptest_config(ProptestConfig {
        cases: 256,
        fork: true,
        timeout: 1_000,
        ..ProptestConfig::default()
    })]

    #[test]
    fn order_codec_roundtrips(order in small_order()) {
        let bytes = encode(&order);
        let decoded = decode(&bytes).expect("our own encoder round-trips");
        prop_assert_eq!(decoded, order);
    }
}

// ---------------------------------------------------------------------------
// Regression: a once-shrunk failure promoted to a named unit test
// ---------------------------------------------------------------------------
//
// When proptest finds a counter-example, it writes the seed to
// `proptest-regressions/order.txt`. The seed file is the backstop;
// the named test below is the system of record. The shrunk value
// is pinned and the bug is documented in the comment.

#[test]
fn regression_qty_999_truncates_item() {
    // Reported by proptest 2026-05-27. The encoder previously
    // truncated `item` to 7 bytes when `qty == 999`, dropping the
    // last character. See PR #42.
    let order = Order { id: 1, item: "abcdefgh".into(), qty: 999 };
    let bytes = encode(&order);
    let decoded = decode(&bytes).expect("decoder accepts our output");
    assert_eq!(decoded, order);
}

// ---------------------------------------------------------------------------
// Anti-pattern (kept for contrast, not for use)
// ---------------------------------------------------------------------------
//
// Do not write this. The .unwrap() bypasses shrinking, the filter
// burns the rejection budget, and the property only checks that
// the code does not panic.
//
// proptest! {
//     #[test]
//     fn order_codec_doesnt_panic(
//         id in any::<u64>().prop_filter("nonzero", |id| *id != 0),
//         item in "[a-z]*",
//         qty in any::<u32>(),
//     ) {
//         let bytes = encode(&Order { id, item, qty });
//         let _ = decode(&bytes).unwrap();
//     }
// }
