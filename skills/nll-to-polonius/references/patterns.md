# Pattern catalogue

Contents:

1. Candidate borrowing shapes
2. Suspect workarounds and compatible alternatives
3. Constraints the checker does not remove
4. Acceptance evidence
5. The discriminator

The examples below are illustrative shapes, not a record of compiler runs.
Use complete owning types and relevant callers when verifying them. Select
Alpha with `-Zpolonius=next` and NLL with `-Zpolonius=off` on the same pinned
nightly, following [verification.md](verification.md). An unflagged nightly
is not an NLL control. The linked Peregrine archive supplies dated evidence
for specific fixtures, not every possible variation here.

## 1. Candidate borrowing shapes

### 1.1 Conditional early return of a borrow (NLL problem case 3)

```rust
fn get_or_insert<'m>(
    map: &'m mut HashMap<String, Config>,
    key: &str,
) -> &'m mut Config {
    if let Some(config) = map.get_mut(key) {
        return config;
    }
    map.insert(key.to_owned(), Config::default());
    map.get_mut(key).expect("just inserted")
}
```

The returned reference ties the hit-path loan to the caller's lifetime.
NLL can retain that loan across the miss path, rejecting the later mutable
borrow. Alpha can distinguish the path where the loan escaped from the
path where it did not. Verify the actual expression, not just its label.

This form performs one map lookup on a hit and three map operations on a
miss: initial lookup, insertion, and final lookup. Using `Entry` on the miss
path can combine insertion and access. A standard entry-based baseline
already returns a mutable reference under NLL; its different trade-off is
owning the key even on hits. Compare both hit and miss workloads.

### 1.2 Borrow on success, error context on failure

```rust
fn lookup(&mut self, key: &str) -> Result<&mut Entry, LookupError> {
    match self.entries.get_mut(key) {
        Some(entry) => Ok(entry),
        None => Err(LookupError::new(self.describe_context(key))),
    }
}
```

Here the failure arm borrows the owner, while the success arm returns a
mutable borrow from it. This may be a case-3-style candidate. If the error
uses only an independent field or owned input, the equivalent expression
may already work under NLL. Do not assume every `ok_or_else` conflict needs
Polonius, or that every restructuring performs eager work.

### 1.3 Lending-iterator loops with conditional escape

```rust
fn first_matching<'c>(
    cursor: &'c mut Cursor,
    predicate: impl Fn(&Item) -> bool,
) -> Option<&'c mut Item> {
    while let Some(item) = cursor.next() {
        if predicate(item) {
            return Some(item);
        }
    }
    None
}
```

A lending cursor's `next(&mut self) -> Option<&mut Item>` borrows from the
cursor. A conditional return can make NLL retain the loan across another
iteration. This is a candidate, not permission to classify every back-edge
as either accepted or rejected. Compile the complete cursor and callers;
compare with the stronger lifetime/flow requirements in section 3.2.

### 1.4 Scan then mutate, returning a reference

```rust
fn find_or_push(items: &mut Vec<Widget>, id: u32) -> &mut Widget {
    for widget in items.iter_mut() {
        if widget.id == id {
            return widget;
        }
    }
    items.push(Widget::new(id));
    items.last_mut().expect("just pushed")
}
```

The search loan escapes only when a matching widget exists. This is another
candidate for path-sensitive reasoning. Compare against an NLL-compatible
index search followed by indexing. `iter().position()` plus indexing a
`Vec` does not require a second linear traversal; do not inflate the
baseline's cost. Persistent indices may also be part of the data model.

## 2. Suspect workarounds and compatible alternatives

### 2.1 Double lookup

```rust
if map.contains_key(key) {
    return Ok(map.get_mut(key).expect("checked above"));
}
map.insert(key.to_owned(), make_default()?);
Ok(map.get_mut(key).expect("just inserted"))
```

This has two hit-path lookups. An early borrowed return may eliminate one,
subject to the explicit checker comparison. In contrast, `contains_key`
followed by insertion with **no escaping reference** is already NLL-compatible.
Duplicate detection and write-only guards are not inherently workarounds.

### 2.2 `entry()` with an owned key

```rust
map.entry(key.clone()).or_insert_with(Default::default)
```

The entry API requires ownership of its key, but already returns a borrow.
Inspect whether the caller needs that borrow. A borrowed lookup returning an
owned or shared handle may remove the hit-path key allocation under NLL.
A write-only guard can use `contains_key` and construct the key on a miss.
Consider existing borrowed-entry APIs where appropriate to the dependency
policy, and measure key costs rather than counting `.clone()` calls.

### 2.3 Clone to shorten access

```rust
let name = self.config.name.clone();
self.apply(&name)?;
```

If `apply(&mut self, ...)` overlaps the borrowed field while that reference
is still used, merely replacing the clone with `&self.config.name` creates a
genuine conflict under either checker. A narrower method taking disjoint
fields may resolve it under both. Only an actual relevant NLL rejection
paired with Alpha acceptance demonstrates checker dependence.

### 2.4 Index-returning helpers

```rust
fn find_slot(&self, id: u32) -> Option<usize> { /* ... */ }
```

The index may allow later access after another operation, express persistent
identity, or avoid tying an object to a registry lock. A returned reference
may be simpler when callers immediately need borrowed access, but do not
invent that requirement. Inspect callers and invalidation rules.

### 2.5 Scopes and explicit `drop()`

Some scope blocks predate NLL and no longer shorten a borrow usefully.
Others deliberately release guards, close resources, or determine destructor
order. Verify the dropped type and observable behaviour before removal.
Compiling after removing a scope does not prove its semantics were irrelevant.

### 2.6 Precomputed error context

```rust
let context = self.describe(key);
let entry = self.map.get_mut(key).ok_or(LookupError::new(context))?;
```

Try a late error branch only if eager construction is unnecessary to the
contract. Section 1.2 describes a possible checker-sensitive case. Preserve
error precedence and side effects; benchmark claimed savings.

## 3. Constraints the checker does not remove

### 3.1 Overlapping exclusive access

Polonius does not permit two overlapping mutable borrows used at once, or
a shared borrow used while overlapping exclusive access occurs. Multiple
shared borrows and disjoint field borrows are valid counterexamples to the
claim that "two references alive at once" are inherently invalid.

Use the appropriate owner, guard scope, field split, `split_at_mut`, or
interior-mutability abstraction. Preserve snapshots that establish iteration
or queued-configuration semantics and release locks before callbacks.

### 3.2 More demanding loop-carried reborrows

Some patterns need more than Alpha's current analysis. For example, an
iterative linked-list truncation may retain a conditional reborrow across
the back-edge and then overwrite its parent:

```rust
fn remove_last_node<T>(mut node_ref: &mut List<T>) {
    loop {
        let next_ref = &mut node_ref.as_mut().unwrap().next;
        if next_ref.is_some() {
            node_ref = next_ref;
        } else {
            break;
        }
    }
    *node_ref = None;
}
```

This sketch needs its complete `List` definition and a pinned reproduction.
Do not generalize from a historical rejection to every loop or promise that
Alpha accepts everything the legacy datalog checker accepts. Record the
specific limitation and rerun when compiler versions change.

### 3.3 Lifetime boundaries, async, and type-system features

References can cross `.await` under NLL when their owners live long enough.
Disjoint-field phase views are an example. Detached tasks and retained
callbacks must satisfy their actual lifetime bounds; the checker cannot
extend the backing storage's lifetime. Scoped threads may borrow too.

Polonius does not change `Send`, `Sync`, trait-object compatibility, closure
capture rules, or self-reference requirements. Test the precise constraint
instead of putting all async or closure-based code in a reject/reject row.
Changing the trait solver is a separate experiment.

## 4. Acceptance evidence

The [Peregrine probe archive][peregrine] records these results on
`nightly-2026-08-27`, observed 2026-09-20, with both solver settings. They
are historical results for those fixtures, not fresh runs of these sketches.

| Archived shape | NLL `off` | Alpha `next` |
| --- | --- | --- |
| Fallible cache, branch before borrowing | Accept | Accept |
| Fallible cache, early returned borrow | E0502 | Accept |
| Map cache, standard entry API | Accept | Accept |
| Map cache, early borrowed hit then entry | E0499 | Accept |
| Disjoint field views across await | Accept | Accept |
| Overlapping exclusive borrows | E0499 | E0499 |

The archive found no solver-specific acceptance benefit. Preserve positive
and negative controls in a new experiment. Do not turn an intended increase
in accepted programs into a guarantee that an experimental compiler has no
regressions, bugs, or tooling costs.

## 5. The discriminator

At each suspect site:

1. Identify the actual caller contract and the best compatible alternative.
2. Ask whether a loan escapes only on another path, or whether overlapping
   exclusive access really occurs while another reference is used.
3. Check owner lifetimes, guards, snapshots, failure atomicity, and identity.
   The presence of a loop, `.await`, a clone, or an ID is not a verdict.
4. Compile the proposed replacement under explicit `off` and `next` using
   [verification.md](verification.md). Investigate non-borrow failures.
5. Record checker-independent improvement, demonstrated checker dependence,
   rejected formulation, or untested hypothesis. No category has a quota.

[peregrine]: https://github.com/leynos/peregrine-web/blob/3d9a2bd9f7137e38d3f5eb5835f0364be9a82036/docs/compiler-probe-evidence.md
