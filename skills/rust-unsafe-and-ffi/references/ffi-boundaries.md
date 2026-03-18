# FFI Boundaries

Spell out these contracts:

- who allocates and who frees,
- whether pointers may be null,
- required alignment and layout,
- string encoding and termination,
- thread-safety expectations,
- whether panics may cross the boundary, which should normally be "no".

Unsafe FFI is usually acceptable when the boundary is tiny and the wrapper is
strict.
