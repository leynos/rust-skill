# Pattern catalogue

Contents:

1. Patterns Polonius newly permits
2. Defensive patterns that Polonius retires
3. Look-alikes Polonius does not fix
4. Acceptance matrix for the alpha analysis
5. The discriminator, restated

Every "accepted under Polonius" claim below refers to the alpha analysis
(`-Zpolonius=next`). Verify unfamiliar shapes by compiling a minimal
reproduction; the analysis is still evolving and this document will age.

## 1. Patterns Polonius newly permits

### 1.1 Conditional early return of a borrow (NLL problem case 3)

The canonical case. NLL computes one lifetime per borrow across the whole
function; a borrow returned from one path is treated as live on all paths,
so the miss path cannot re-borrow.

```rust
// Rejected by NLL, accepted by Polonius:
fn get_or_insert<'m>(
    map: &'m mut HashMap<String, Config>,
    key: &str,
) -> &'m mut Config {
    if let Some(cfg) = map.get_mut(key) {
        return cfg;                              // borrow escapes here only
    }
    map.insert(key.to_owned(), Config::default()); // NLL: E0499/E0502 here
    map.get_mut(key).expect("just inserted")
}
```

NLL error: `cannot borrow *map as mutable more than once at a time`,
pointing at the `insert`, because the `get_mut` borrow's region includes the
function's return and therefore the entire body. Polonius reasons per
program point: on the fall-through path the loan from `get_mut` is dead, so
the `insert` is legal.

Runtime consequence: one lookup on the hit path, and the key is cloned only
on the miss path. Contrast with the NLL-era workarounds in §2.1 and §2.2.

Note the residual double work on the *miss* path (`insert` then a second
`get_mut`): Polonius does not remove that, because `insert` returns the
previous value, not a reference to the new one. The win is confined to the
hit path and the conditional key clone — state this precisely when
estimating benefit.

### 1.2 Borrow live on the success path, second borrow on the failure path

A variant of 1.1 that appears constantly in error handling:

```rust
// Rejected by NLL, accepted by Polonius:
fn lookup(&mut self, key: &str) -> Result<&mut Entry, LookupError> {
    match self.entries.get_mut(key) {
        Some(entry) => Ok(entry),
        None => Err(LookupError::new(self.describe_context(key))),
        //                           ^^^^ NLL: cannot borrow `*self`
    }
}
```

The `None` arm borrows `self` again while NLL still considers the
`get_mut` loan live (it flows into the return type). Polonius sees the loan
dead on the `None` path. The NLL-era workarounds — precomputing the error
context before the lookup, or restructuring into two functions — do
speculative work on the hot path and can be retired.

### 1.3 Lending-iterator loops with conditional escape

The shape tracked as rust-lang/rust#92985: a hand-rolled cursor whose
`next(&mut self) -> Option<&mut T>` result conditionally escapes the loop.

```rust
// Rejected by NLL, accepted by Polonius:
fn first_matching<'c>(
    cursor: &'c mut Cursor,
    pred: impl Fn(&Item) -> bool,
) -> Option<&'c mut Item> {
    while let Some(item) = cursor.next() {
        if pred(item) {
            return Some(item);
        }
    }                       // NLL: `*cursor` still borrowed on next iteration
    None
}
```

Under NLL the returned borrow forces each iteration's loan to outlive the
loop, conflicting with the next `cursor.next()` call. Polonius kills the
loan on the non-escaping path. This is the pattern that unblocks
`LendingIterator`-style APIs; if the codebase contains a collect-then-index
or index-based re-fetch workaround around a streaming API, this is the
rewrite target.

### 1.4 Scan-then-mutate returning a reference

```rust
// Rejected by NLL, accepted by Polonius:
fn find_or_push<'v>(items: &'v mut Vec<Widget>, id: u32) -> &'v mut Widget {
    for w in items.iter_mut() {
        if w.id == id {
            return w;
        }
    }
    items.push(Widget::new(id));   // NLL: `*items` still mutably borrowed
    items.last_mut().expect("just pushed")
}
```

The NLL-era workaround returns an index (`fn find_or_push(..) -> usize`)
and forces every caller to re-index, or uses `iter().position()` followed
by a second traversal. Both retire under Polonius.

## 2. Defensive patterns that Polonius retires

These are the shapes coding agents (and defensively trained humans) emit to
route around §1. Each entry gives the tell, the direct form, and the
conditions under which the rewrite actually pays.

### 2.1 Double lookup

```rust
// Tell:
if map.contains_key(key) {
    return Ok(map.get_mut(key).expect("checked above"));
}
map.insert(key.to_owned(), make_default()?);
Ok(map.get_mut(key).expect("just inserted"))
```

Two hash-and-compare traversals on the hit path plus an `expect` that
encodes a proof the compiler could not check. Rewrite to §1.1. **Caveat:**
a bare `contains_key` + `insert` with no reference kept (write-only
guarding) already compiles under NLL and is not a Polonius candidate — see
worked example W3.

### 2.2 `entry()` with an unconditionally cloned key

```rust
// Tell:
map.entry(key.clone()).or_insert_with(Default::default)
```

The entry API demands an owned key even when the entry already exists, so
hit-dominant workloads pay a clone per call. It was the sanctioned NLL-era
answer to §1.1, traded against §2.1. Under Polonius the direct form clones
only on miss. The rewrite pays when (a) the key clone is non-trivial
(String, Vec, PathBuf — not Copy types) and (b) hits dominate. Where
`or_insert_with` closures capture environment borrows that fight the entry
borrow, the direct form also dissolves that knot.

### 2.3 Clone-to-truncate-a-borrow

```rust
// Tell:
let name = self.config.name.clone();   // clone exists only to end the borrow
self.apply(&name)?;                    // &mut self method
```

Classify carefully. If the clone breaks a borrow that would otherwise be
*live at the same instant* as the `&mut self` call, the clone is an
aliasing fix and Polonius changes nothing (§3.1). If the clone breaks a
borrow that NLL merely *over-extends* — typically because the borrowed
value flows into a return or a conditional escape — it is a §1 shape in
disguise. Test: comment out the clone, take a reference instead, and
compile under both checkers. Only sites that fail NLL and pass Polonius
qualify.

### 2.4 Index-returning helpers

```rust
// Tell:
fn find_slot(&self, id: u32) -> Option<usize> { ... }
// callers: let i = self.find_slot(id)?; let slot = &mut self.slots[i];
```

Indices as ersatz references, with bounds checks and staleness hazards the
type system no longer sees. Where the helper exists to avoid §1.4, restore
the reference-returning signature. Where indices are stored across calls or
serialized, they are a data-model choice; leave them.

### 2.5 Scope blocks and `drop()` calls that end borrows

```rust
// Tell:
let ctx = { let e = self.map.get(k); e.map(Ctx::of) }; // block to kill borrow
// or:
drop(entries);
self.rebuild();
```

Most of these became unnecessary when NLL itself landed and are cargo cult.
A minority guard genuine §1 shapes. Either way the block or `drop` can
usually go; verify with a compile under the target checker and keep any
`drop` whose purpose is a Drop side effect (locks, files) — those are
semantic, not borrowck appeasement. Distinguish by the dropped type.

### 2.6 Precomputed error context

```rust
// Tell:
let context = self.describe(key);       // computed even on the happy path
let entry = self.map.get_mut(key).ok_or(LookupError::new(context))?;
```

The eager `describe` exists because §1.2 blocked the lazy form. Rewrite to
match-with-late-context. The win is real when context construction
allocates or formats.

## 3. Look-alikes Polonius does not fix

Rewriting these breaks the build and burns trust. Recognize and refuse.

### 3.1 Simultaneous borrows

Two references genuinely alive at once — iterating a collection while
inserting into it, holding `&self.a` while calling a `&mut self` method
that could touch `a`, passing `&mut x` twice. These are aliasing
violations; the clone/split/restructure workarounds remain load-bearing.
`Vec::split_at_mut`, taking fields apart before the call, and interior
mutability all stay.

### 3.2 Loop-carried conditional reborrow (full flow-sensitivity)

The alpha analysis explicitly excludes patterns like the iterative
linked-list truncation:

```rust
// Still rejected by polonius alpha:
fn remove_last_node<T>(mut node_ref: &mut List<T>) {
    loop {
        let next_ref = &mut node_ref.as_mut().unwrap().next;
        if next_ref.is_some() {
            node_ref = next_ref;
        } else {
            break;
        }
    }
    *node_ref = None;   // ERROR: `*node_ref` is borrowed
}
```

The recursive formulation remains the workaround. Similarly, patterns
requiring reasoning about invariant lifetimes across `Result` branches
stay rejected. If a comment in the codebase blames the borrow checker for
one of these, update the comment to name the limitation precisely; do not
promise Polonius relief.

### 3.3 Self-references, async-held borrows, and closure captures

Different mechanisms entirely (no way to name the lifetime; the state
machine holds the borrow; closure capture granularity). Out of scope.

## 4. Acceptance matrix (polonius alpha, mid-2026)

| Shape | NLL | Polonius alpha |
| --- | --- | --- |
| §1.1 conditional early return of borrow (case 3) | reject | **accept** |
| §1.2 borrow on success path, re-borrow on failure path | reject | **accept** |
| §1.3 lending-iterator conditional escape (#92985) | reject | **accept** |
| §1.4 scan-then-mutate returning reference | reject | **accept** |
| §3.1 simultaneous borrows | reject | reject |
| §3.2 loop-carried reborrow | reject | reject (needs flow-sensitivity) |
| §3.3 self-referential / async-held / closure-capture | reject | reject |

The alpha is a superset of NLL: nothing moves from accept to reject.

## 5. The discriminator, restated

At each suspect site, ask in order:

1. **Is the conflicting borrow live only because it escapes on *another*
   path (return, break-with-value, assignment to an outer binding)?**
   Yes → §1 shape, candidate.
2. **Are both borrows used on the *same* path?** Yes → aliasing, refuse
   (§3.1).
3. **Does the borrow travel around a loop back-edge before the conflict?**
   Yes → probably §3.2, refuse unless a minimal repro compiles under the
   flag.
4. **When in doubt, compile.** A ten-line repro under
   `RUSTFLAGS="-Zpolonius=next" cargo +nightly check` settles what no
   amount of reasoning from this document can.
