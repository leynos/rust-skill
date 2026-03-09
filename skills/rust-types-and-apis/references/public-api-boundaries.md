# Public API Boundaries

Public APIs should expose intent, not scaffolding.

Defaults:

- accept slices and `&str` instead of `&Vec<T>` and `&String`,
- return named domain types instead of tuples once meaning matters,
- hide helper traits, builder internals, and temporary allocation choices,
- document invariants in the type or constructor, not only in prose,
- add `#[non_exhaustive]` or sealed traits when future evolution matters.

If an internal refactor would be a breaking change, the public surface is too
tightly coupled to the implementation.
