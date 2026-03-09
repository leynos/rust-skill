---
name: rust-unsafe-and-ffi
description: Use for unsafe Rust, raw pointers, `MaybeUninit`, `NonNull`, FFI, ABI boundaries, layout guarantees, and soundness review.
globs: ["**/Cargo.toml", "**/*.rs"]
---

# Rust Unsafe and FFI

Use this when the code must uphold invariants the compiler cannot check.

## Working stance

- Safe wrapper first; `unsafe` is the narrow implementation detail.
- Write the invariant list before writing the block.
- Every `unsafe` block should justify itself in plain language.
- FFI boundaries must define ownership, lifetime, layout, and panic policy.
- If a safe design is available and fast enough, prefer it.

## Decision surface

- Non-null raw ownership handle: use `NonNull<T>`.
- Deferred initialization: use `MaybeUninit<T>`.
- C ABI interop: use an explicit `repr(C)` contract where required.
- Public low-level capability: build a safe wrapper and expose a narrow
  `unsafe fn` only when the caller truly must uphold the contract.
- Sharing across threads: prove `Send` and `Sync`; never assume them.

## Red flags

- `unsafe` appears only to silence the borrow checker,
- pointer validity and aliasing rules are not written down,
- `CString::as_ptr()` outlives the owning `CString`,
- FFI code can panic across the boundary,
- manual `Send` or `Sync` impls appear without a crisp argument.

Read [safety-comment-template.md](references/safety-comment-template.md),
[ffi-boundaries.md](references/ffi-boundaries.md), and
[maybeuninit-and-nonnull.md](references/maybeuninit-and-nonnull.md) before
adding new unsafe blocks or reviewing old ones.
