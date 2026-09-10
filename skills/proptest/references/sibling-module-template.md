# Sibling property-test module template

The shape that passes review first time in repositories with a per-file
line cap, mandatory module docs, and a Clippy policy applied to tests.
Adapt the names; keep the structure.

## Files

```text
src/
└── canonical/
    ├── mod.rs                     # production code
    ├── tests.rs                   # rstest examples (existing)
    ├── prop_tests.rs              # properties only
    └── prop_strategies.rs         # strategies only
```

In `mod.rs`:

```rust
#[cfg(test)]
mod prop_strategies;
#[cfg(test)]
mod prop_tests;
#[cfg(test)]
mod tests;
```

## `prop_strategies.rs`

```rust
//! Strategies for the canonicalization properties.
//!
//! Every strategy is total: each drawn value is a valid input by
//! construction, so the properties never filter.

use proptest::prelude::*;

use super::{Segment, MAX_SEGMENTS};

/// A path segment that cannot collide with reserved device names.
pub(super) fn segment() -> impl Strategy<Value = Segment> {
    "[a-z]{1,5}".prop_map(|s| Segment::new(format!("seg_{s}")))
}

/// A non-empty path within the production bound.
pub(super) fn path() -> impl Strategy<Value = Vec<Segment>> {
    prop::collection::vec(segment(), 1..=MAX_SEGMENTS)
}

/// Every variant, derived from the canonical constant so a new variant
/// is generated automatically.
pub(super) fn mode() -> impl Strategy<Value = super::Mode> {
    prop::sample::select(super::Mode::ALL.to_vec())
}
```

## `prop_tests.rs`

```rust
//! Property tests for canonicalization.
//!
//! Oracle: the `reference::canonicalize_slow` brute-force implementation
//! in `tests/support`. Case counts come from `PROPTEST_CASES`.

use proptest::prelude::*;

use super::prop_strategies::{mode, path};
use super::{canonicalize, Mode};
use crate::test_support::reference;

proptest! {
    #[test]
    fn canonicalize_is_idempotent(p in path(), m in mode()) {
        let once = canonicalize(&p, m);
        let twice = canonicalize(&once, m);
        prop_assert_eq!(twice, once);
    }

    #[test]
    fn canonicalize_matches_reference(p in path(), m in mode()) {
        prop_assert_eq!(canonicalize(&p, m), reference::canonicalize_slow(&p, m));
    }

    #[test]
    fn canonicalize_preserves_length_bound(p in path(), m in mode()) {
        let out = canonicalize(&p, m);
        prop_assert!(out.len() <= p.len(), "output grew: {} > {}", out.len(), p.len());
    }
}
```

Points that reviewers check against this shape:

- each function inside `proptest!` carries `#[test]`;
- every generated binding reaches an assertion;
- the oracle is structurally different from the code under test;
- no `.unwrap()`/`.expect()` unless the workspace lint policy allows it;
  fallible setup returns `TestCaseError` through `?` on `Result<_, TestCaseError>`
  helpers;
- no `prop_assume!` on outputs; preconditions, if any, precede the call;
- no branching in the body beyond a single `match` on a generated enum;
- the module doc names the oracle and the tiering variable.

## Optional configuration

Only when the default 256 cases is wrong for a documented reason:

```rust
proptest! {
    #![proptest_config(ProptestConfig {
        cases: match std::env::var("PROPTEST_CASES") {
            Ok(v) => match v.parse::<u32>() {
                Ok(n) if n > 0 => n,
                _ => panic!(
                    "PROPTEST_CASES must be a positive integer, got {v:?}"
                ),
            },
            Err(_) => 256,
        },
        .. ProptestConfig::default()
    })]
    // ...
}
```

Prefer the repository's shared profile helper if one exists (for
example a `ProptestRunProfile` that reads `PROPTEST_CASES` and a fork
flag once) over local environment parsing. A malformed value fails
loudly at configuration time, outside any property body, rather than
silently running 256 cases.

## Scope statement when no property is warranted

When a change introduces no invariant over a range, say so where the
reviewer will look, in one or two sentences:

> Property tests: not added. The new `Mode` parser accepts exactly four
> literals and rejects everything else; the four success cases and three
> representative failures are enumerated in `tests.rs` and run on every
> build, so a generator would add no coverage.
