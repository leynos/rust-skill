# API evolution playbook

Mode-E guidance: evolving internal APIs from the owned-value style NLL
imposed toward the borrow-centric model Polonius enables. This file covers
the target shapes (§1), the constraints that survive Polonius and where
owned style therefore remains correct (§2), sequencing (§3), and progress
measurement (§4).

The organizing question for every API under review:

> **Would the natural borrow-returning design of this API fail NLL but
> pass Polonius?** Fail-NLL/pass-Polonius → evolution target.
> Pass-both → the old form was habit; evolve freely, no toolchain caveat.
> Fail-both → the owned style is load-bearing (§2); record why and keep it.

"Natural" means the signature you would write if the borrow checker were
not in the room: lookups return references, mutation happens in place,
errors build context lazily, traversal lends.

## 1. Target shapes

### 1.1 Registries, caches, interners → get-or-create returning `&mut V`

The NLL-era registry hands back owned tokens — clones, ids, hashes — and
callers re-look-up or clone-out to work with the value. The Polonius-era
form:

```rust
pub fn get_or_create(&mut self, key: &Key) -> Result<&mut Entry, Error> {
    if let Some(e) = self.entries.get_mut(key) {
        return Ok(e);
    }
    let e = Entry::build(key, &self.context)?;   // may borrow &self fields
    self.entries.insert(key.clone(), e);
    Ok(self.entries.get_mut(key).expect("just inserted"))
}
```

Single lookup on hit, key cloned only on miss, error path free to borrow
`self` (patterns.md §1.1–1.2). Callers mutate in place instead of
clone-modify-writeback. Where the old API returned an id *because the id
is data* (serialized, stored in another structure, sent cross-thread),
keep the id as the persistent identity but add the reference-returning
accessor for the mutation paths.

### 1.2 Id/index indirection → references at function boundaries

Classify every id-returning finder by what the id is *for*:

- **Borrow-dodging id** — exists so the caller can end the borrow and
  re-index later, always immediately dereferenced. Replace with the
  reference-returning form (patterns.md §1.4). The bounds check, the
  `expect`, and the staleness hazard all disappear into the type system.
- **Data id** — persisted, serialized, compared, stored in other
  structures, or crossing threads. Keep. Ids as identity are a data-model
  choice Polonius has no opinion on.

### 1.3 Clone-modify-writeback → in-place mutation

```rust
// NLL-era:
let mut cfg = self.configs.get(name).cloned().unwrap_or_default();
cfg.apply(overrides);
self.configs.insert(name.to_owned(), cfg);

// Polonius-era:
self.config_mut(name).apply(overrides);   // §1.1-shaped accessor
```

The scanner surfaces these as `get(..).cloned()`/`.clone()` followed by
`insert` on the same container. Each one converted removes an allocation,
a full-value copy, and a window in which two versions of the truth exist.

### 1.4 Snapshot-collect loops → lending traversal

The NLL-era shape collects keys or clones items into a `Vec` purely so the
loop body can borrow the container again:

```rust
// NLL-era:
let names: Vec<String> = self.nodes.keys().cloned().collect();
for name in names {
    if self.needs_rebuild(&name) { ... }
}
```

Convert **only** when the borrow conflict is a lifetime artefact — e.g.
the body's second borrow is shared, or the mutation happens after the
loop, or the escape is conditional (patterns.md §1.3). When the body
genuinely mutates the container being iterated, that is aliasing (§2.1)
and the snapshot stays — though it can often shrink from cloned values to
collected keys.

### 1.5 Eager error context → lazy

Every `let context = self.describe(...)` computed before a lookup so the
failure arm has something to say (patterns.md §1.2 / §2.6) moves into the
failure arm. In hot paths that format or allocate, this is a measurable
win; everywhere it is a readability win — the happy path stops paying for
the sad one.

### 1.6 Builders and aggregates → on-demand `&mut` sub-access

NLL punished `fn section_mut(&mut self, name: &str) -> &mut Section` on
builders whenever creation-on-first-access was involved, so builders grew
add/replace/finish choreography. Under Polonius the accessor is §1.1 and
builders can expose their parts directly.

## 2. Where owned style remains correct

These are permanent constraints, not NLL residue. Converting them breaks
the build or the design; the audit records them as `POLONIUS-REFUSED`
with the constraint named.

### 2.1 Aliasing

Two borrows alive at the same instant: iterating while inserting, holding
`&self.a` across a `&mut self` call that reaches `a`, distributing `&mut`
into parallel workers. Splitting borrows, taking fields apart, snapshot
iteration over the mutation set, and interior mutability all stay.
Framework-mediated aliasing (ECS write-queries, incremental-computation
handles) is this category: the framework's handle discipline *is* the
aliasing solution — do not fight it with references of your own.

### 2.2 Suspension points

References held across `.await`, event-loop turns, or callback
registration make the holder self-referential or infect it with
lifetimes it cannot honour. Daemons, actor loops, and async services keep
owned messages at their boundaries. Borrow-centric design applies *within*
a turn, not across turns.

### 2.3 Thread and process boundaries

`Send`/`Sync` and serialization want owned data. Ids and owned messages at
these boundaries are correct.

### 2.4 Lifetime infection of struct fields

Returning `&mut V` from a method is cheap; *storing* `&'a V` in a struct
propagates `'a` through every containing type. The working rule:
borrow-centric at function signatures, ownership at struct fields.
Arena-style designs are the deliberate exception, and adopting one is an
architecture decision beyond this skill's remit — flag it, do not do it.

## 3. Sequencing

1. **Leaf accessors first.** Introduce the §1.1-shaped accessor alongside
   the old API; do not delete anything yet.
2. **Migrate call sites** to the accessor, converting
   clone-modify-writeback and re-lookup sequences as encountered. One API
   per commit; test failures then localize.
3. **Delete the superseded API** once `rg` finds no callers. Pre-1.0 and
   self-consumed means no deprecation period — dead code is worse than
   churn.
4. **Cascade outward.** Each converted accessor typically exposes the next
   layer's writeback pattern; repeat until the design-pressure scan comes
   back quiet or everything remaining is §2.

Resist the urge to convert an entire module in one commit. The
fail-NLL/pass-Polonius check in the workflow's phase 4 is per-change; a
mixed commit makes its classification meaningless.

## 4. Measuring progress

Crude but effective, per module:

```bash
rg --count --glob '*.rs' '\.clone\(\)' src/ | sort -t: -k2 -rn
```

Track the count per audit pass. It will not reach zero — §2 clones are
correct — but the trajectory and the per-module distribution show where
NLL pressure concentrated and whether the evolution is reaching it.
Complement with the scanner's clone-modify-writeback section, which
should trend to empty, and with allocation profiles where the codebase
already has benchmarks.
