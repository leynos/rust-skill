# `MaybeUninit` and `NonNull`

Use `MaybeUninit<T>` for staged initialization and arrays or buffers that are
not fully initialized yet.

Use `NonNull<T>` when null is invalid and you want that invariant expressed in
the type.

Both types are tools for narrowing invariants. They do not remove the need to
prove initialization, aliasing, and lifetime correctness.
