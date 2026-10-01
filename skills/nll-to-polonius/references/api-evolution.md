# API evolution playbook

Mode E permits changing internal interfaces and their callers. It does not
predetermine that a borrowed result is better or that a new compiler is
necessary. Use the [verification protocol](verification.md) to distinguish
an architectural improvement from a checker-dependent one.

For each owning API, ask:

> What ownership contract do the actual callers need, and what is the
> simplest implementation under each checker that preserves that contract?

Compare complete alternatives. Acceptance under both checkers establishes no
Alpha requirement; rejection under both rejects that expression, not every
possible borrowed design. A source review without compilation remains a
hypothesis. Do not infer why an existing API was written from its shape alone.

## 1. Target shapes and compatible alternatives

### 1.1 Registries and caches: return a borrow when callers need one

A conditional borrowed hit followed by creation on a miss is a useful
candidate:

```rust
// Illustrative body: compile the complete owning type and relevant callers.
pub fn get_or_create(&mut self, key: &Key) -> Result<&mut Entry, Error> {
    if let Some(entry) = self.entries.get_mut(key) {
        return Ok(entry);
    }
    let entry = Entry::build(key, &self.context)?;
    self.entries.insert(key.clone(), entry);
    Ok(self.entries.get_mut(key).expect("just inserted"))
}
```

This version has one hit-path lookup and clones the key only on a miss. It
has three map operations on a miss: lookup, insert, and lookup again.
Using `Entry` on the miss path can avoid the final lookup.

Compare against the standard entry API, which already returns `&mut V`
under NLL. For infallible optional caches, try `Option::get_or_insert_with`.
For fallible caches, compare branch-before-borrow and entry-based forms.
A borrowed-key fast path returning an **owned handle** may already work
under NLL because the map borrow does not escape. A write-only caller may
need no returned reference at all.

Do not change duplicate-registration errors into idempotent creation, or
missing-entry errors into lazy spawning, merely to fit this pattern.
Those are behaviour changes, not borrow-checker cleanup.

### 1.2 IDs and indices: distinguish access from identity

An immediately re-indexed result can justify a reference-returning accessor,
but inspect the caller's subsequent mutations and the lifetime of the owner.
A shorter borrow followed by a later lookup can be deliberate.

Keep identities used in persistent state, serialization, comparison, other
collections, queues, or independently scheduled work. A reference borrowed
from a registry behind a lock cannot outlive its guard. An owned/shared
handle that allows lock release may be the correct API even when its result
is used immediately. Add a borrowed accessor only for demonstrated needs.

### 1.3 Clone-modify-writeback: preserve staging semantics

```rust
let mut config = self.configs.get(name).cloned().unwrap_or_default();
config.apply(overrides);
self.configs.insert(name.to_owned(), config);
```

In-place mutation can remove a copy, but it may also remove transactional
isolation, rollback on error or panic, or a deliberate snapshot boundary.
Check the contract before replacing this with an entry or mutable accessor.
Not every clone allocates: shared-pointer cloning and deep payload cloning
have different costs and semantics.

When a function already owns a snapshot, calculate derived information while
borrowing it, then destructure and **move** its fields into the staged state.
When a commit object has no later users, a consuming commit API may borrow
its fields during validation and move them into place afterwards. These are
ordinary ownership-design candidates, not inherently Polonius-dependent.
Preserve the original isolation from live state and failure-path guarantees.

Similarly, a fan-out implementation may clone a record for all but the final
recipient and move the original into that final recipient. Preserve recipient
order and error handling; measure deep-copy savings rather than assuming them.

### 1.4 Snapshots and traversal: inspect mutation and lock boundaries

Collecting keys before traversal might avoid a borrow conflict, establish a
stable iteration set, or release a lock before callbacks. Those are distinct
reasons. Shared access to disjoint state may already permit a direct loop
under NLL; a lending iterator's conditional escape may be checker-dependent.

Do not replace snapshot iteration with callbacks under a held lock, extend
lock duration inadvertently, or change which queued records see a
configuration update. If the loop mutates the traversed collection, identify
the exact overlap and invalidation risk. Field splitting or a smaller snapshot
may help without changing the checker.

### 1.5 Error context: defer only semantically unnecessary work

An early-returning mutable borrow can prevent a later error branch from
borrowing the owner under NLL. This is a candidate for Alpha's more precise
loan analysis. An error closure that captures an independent field or an
owned value may already work under NLL.

Preserve error contents, ordering, side effects, and failure timing. Record
formatting/allocation savings as a hypothesis until measured.

### 1.6 Builders and views: narrow access before changing the compiler

A builder can expose fields through borrowed accessors under either checker.
Creation-on-demand does not by itself establish a Polonius requirement:
standard `Entry` and `Option` APIs already support many such designs.

Field splitting, phase-specific views, consuming finalization, and narrow
constructor injection are architecture decisions available to both compiler
candidates. Do not compare a monolithic NLL context against a split Alpha
context and attribute the resulting improvement to the checker.

## 2. Constraints and legitimate borrowing

### 2.1 Aliasing and guards

Overlapping exclusive borrows remain forbidden. Multiple shared borrows and
exclusive borrows of disjoint fields are not that failure mode.
`split_at_mut`, guard lifetimes, framework query disciplines, and suitably
scoped callbacks can express sound access. A failed attempted rewrite does
not prove that a clone is the only possible implementation.

### 2.2 Awaited calls versus escaping work

Borrowing across `.await` is legal when the backing owner outlives the future
and the other type and executor requirements hold. A request future can loan
disjoint field views to an awaited responder and regain access afterwards.
This already works under NLL; see the Peregrine control in
[worked-examples.md](worked-examples.md).

Detached tasks, retained callbacks, response streams, and queued jobs must
meet their actual lifetime bounds. A request-local reference cannot survive
after its backing storage is destroyed. Owned or shared state often supplies
that lifetime, but the presence of `.await` alone does not require a clone.
Do not equate a compile-only future with a validated `Send` or cancellation
contract.

### 2.3 Threads and processes

Polonius changes neither `Send` nor `Sync`. These traits do not require all
data to be owned: suitably bounded references and scoped threads can work.
A spawning API that requires `'static` must satisfy that bound separately.
Process transport needs an appropriate representation and serialization;
a process boundary is not the same as a Rust borrow-checking boundary.

### 2.4 Borrowed fields and self-reference

Borrowed view structs are legitimate when their owners and scopes are clear.
Their lifetime parameters are a design cost to assess, not evidence of an
invalid design. Storing a reference into the same movable aggregate is a
different problem. Do not add unsafe lifetime extension or an arena redesign
as an incidental Polonius migration.

## 3. Sequencing

1. Record the current contract, representative callers, supported compilers,
   and the best compatible alternative.
2. Change one owning API and its relevant callers as a coherent step. Avoid
   mixing unrelated cleanups with a checker-dependent experiment.
3. Compare baseline and replacement under the explicit controls. Classify
   the replacement, not a whole-crate failure caused by another Alpha site.
4. Test behaviour before deleting superseded code. Do not retain obsolete
   private APIs or dual production implementations merely for the experiment.
5. Follow simplification into callers where it is useful. Stop when the
   benefit disappears or the remaining ownership expresses real contracts.

## 4. Measuring progress

Clone counts and scanner matches identify places to inspect. They do not
measure allocation volume, prove NLL caused a design, or set a removal quota.
Track confirmed checker-dependent changes separately from compatible
refactors and rejected or untested proposals.

Where performance matters, record key sizes, payload sizes, hit/miss ratios,
allocation counts, retained memory, lock duration, throughput, latency, and
compile-time costs. Include miss-heavy workloads. A smaller source-level
clone count can conceal more retained memory or a longer-held lock.
