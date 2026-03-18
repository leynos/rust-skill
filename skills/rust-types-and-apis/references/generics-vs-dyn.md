# Generics vs `dyn`

Use generics when the caller should stay generic too, inlining matters, or the
type relation is part of the API contract.

Use `dyn Trait` when:

- values of different concrete types must share one collection,
- the extension point is intentionally open-ended,
- compile times or binary size matter more than per-call dispatch overhead.

Questions that usually settle it:

- Does the caller care which concrete type came back?
- Is there one implementation per call site, or many at runtime?
- Is object safety already forcing the shape?
