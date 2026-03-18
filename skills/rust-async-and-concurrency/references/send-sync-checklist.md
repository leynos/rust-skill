# `Send` and `Sync` Checklist

Ask these in order:

1. Does this value cross a thread boundary or enter a multithreaded runtime?
2. Is the captured state owned, or does it borrow local stack data?
3. Does any field contain `Rc`, `RefCell`, raw pointers, or thread-affine
   resources?
4. Would a single-thread runtime or dedicated owner task be simpler?

Do not force `Send` with unsafe code unless the thread-safety invariant is
obvious and documented.
