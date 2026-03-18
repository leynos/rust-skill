# Interior Mutability

Use interior mutability when shared access is part of the design, not when a
single-owner model would work.

Choose by context:

- `Cell<T>` for small copyable values.
- `RefCell<T>` for single-thread dynamic borrow checks.
- `Mutex<T>` for cross-thread exclusive mutation.
- `RwLock<T>` when read contention dominates and write rules stay simple.

Questions to ask first:

- Why is the data shared?
- Is the mutation coarse-grained or fine-grained?
- Can ownership move to one task and updates arrive by message instead?

If locking appears in many call sites, the state boundary is probably wrong.
