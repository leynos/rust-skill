# Safety Comment Template

Use comments that name the real invariant, not boilerplate.

```rust
// SAFETY:
// - `ptr` is non-null and points to `len` initialized elements.
// - no mutable aliases exist for the duration of this borrow.
// - the callee does not retain the pointer after return.
```

If the comment cannot be written clearly, the block is probably not ready.
