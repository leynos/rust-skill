# Encapsulation and RAII

Ownership is an architectural lever, not only a memory-management rule. Use it
to decide where decisions live, what can move between modules, and what the
compiler will refuse to let you forget.

## Ownership as decoupling

Move ownership across a boundary when the caller should no longer care about
the value after the call returns. The receiver becomes the sole authority on
its state, lifetime, and clean-up. Two modules that exchange owned values do
not share state; they exchange responsibility.

Borrowing is the opposite: it couples the borrower's scope to the owner's
liveness. Long-lived borrows in public APIs are a coupling decision and
deserve the same scrutiny as any other shared mutable state.

Practical consequences:

- Prefer owned return types at module seams unless the caller has a concrete
  reason to read in place.
- Push lifetimes inward. A struct that stores `&'a T` exports `'a` to every
  caller; a struct that owns `T` does not.
- Reach for `Arc<T>` only when shared ownership is the real model. Otherwise
  one owner with borrowed reads is cheaper and clearer.

## The Mutex/MutexGuard/Drop wireframe

`Mutex<T>` is the canonical example of a safe wrapper over shared mutable
state, and it is built from three cooperating pieces:

- `UnsafeCell<T>` provides the only sound way to mutate through a shared
  reference (`&Self`). See
  [`unsafecell-and-interior-mutability.md`](../../rust-unsafe-and-ffi/references/unsafecell-and-interior-mutability.md)
  for the aliasing rules that make this necessary.
- `MutexGuard<'a, T>` is a borrow-bound smart pointer returned by `lock`. It
  carries the lock state and dereferences to `&mut T` for the guard's
  lifetime.
- `Drop for MutexGuard` releases the lock when the guard goes out of scope.
  Release is tied to scope, not to a `release()` call the caller might
  forget on an unwind or early return.

The same shape (acquire returns a guard; the guard's `Drop` releases the
resource) generalizes to transaction handles, file locks, span guards,
cancellation tokens, and any other resource where forgetting to release is a
bug.

## Red flags worth a second look

- A type exposes both `lock()` and `unlock()` instead of a guard.
- A guard is stored in a field of `'static` lifetime "to keep the lock held".
- Ownership of a resource is split between a constructor that opens it and a
  separate routine the caller must remember to call.
- A type holds `&'a mut T` for convenience and forces every caller to thread
  `'a` through unrelated APIs.

When these appear, the encapsulation is leaking. Wrap the resource in an
owning type whose `Drop` does the right thing, and return guards for any
operation that must be paired with a release.
