# UnsafeCell and Interior Mutability

`UnsafeCell<T>` is the only sound way to obtain a `*mut T` from `&UnsafeCell<T>`.
Every safe interior-mutability primitive in `std`—`Cell`, `RefCell`, `Mutex`,
`RwLock`, `OnceCell`, `Atomic*`—is built on top of it. If you reach for
interior mutability without one of those wrappers, you are committing to
proving that your bespoke construction upholds the same rules.

## Why `UnsafeCell` exists

Rust's aliasing model permits the compiler (and LLVM) to assume that a value
behind `&T` does not change for the duration of the borrow. That assumption
becomes `noalias` and `readonly` hints in codegen. Mutating through `&T`
without `UnsafeCell` is therefore not "merely" undefined behaviour (UB) at
the language level—the optimizer can and will reorder reads, hoist them out
of loops, and fold them with stale values.

`UnsafeCell<T>` opts the field out of those assumptions. It is the single
exception the language carves out, and it is opaque on purpose: it has no
safe API beyond `get(&self) -> *mut T` and `get_mut(&mut self) -> &mut T`.
Everything else lives in the wrapper crate or in `std`.

## The invariants the wrapper must enforce

A correct interior-mutability wrapper must guarantee, for every read or write
it performs through `UnsafeCell::get`:

- No `&T` and `&mut T` to the same value coexist at any instant.
- No two `&mut T` to the same value coexist at any instant.
- For cross-thread access, ordering is established by `Sync` and by the
  primitives the wrapper uses (atomics, OS locks, RCU schemes, and so on).
- Reads and writes do not violate the validity invariants of `T` itself (for
  example, a partially initialized `Box<T>` is never observed).

If any of these can be broken, the wrapper is unsound and the bug surfaces
as miscompilation or torn reads, not as a panic.

## Common UB pitfalls

- Casting `&T` to `&mut T` (or to `*mut T` and writing through it) without
  `UnsafeCell`. The optimizer is allowed to assume the value did not change.
- Holding a `&T` that aliases an active `&mut T` to the same `UnsafeCell`
  field, even briefly. The wrapper must serialize access.
- Implementing `Sync` for a wrapper whose internal pointer dance is not
  actually thread-safe. `Sync` is a load-bearing claim, not a marker.
- Returning a guard or reference whose lifetime outlives the locking state
  it depends on (for example, by transmuting the lifetime).
- Forgetting that `Drop` of `T` can re-enter the wrapper. A `Drop` panic
  while a borrow is outstanding may strand the lock and corrupt later
  accesses.

## Reaching for verification

Hand-written interior-mutability code is precisely the situation where
[Miri](../../rust-verification/SKILL.md) (for UB detection) and
[`loom`](../../rust-verification/SKILL.md) (for exhaustive interleaving of
small concurrent primitives) earn their keep. Run them before trusting any
new wrapper in production.
