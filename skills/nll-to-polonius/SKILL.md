---
name: nll-to-polonius
description: >-
  Migrate a Rust codebase to the Polonius borrow checker (location-sensitive
  analysis, nightly flag -Zpolonius=next) and evolve owned-value internal
  APIs into the reference-returning, borrow-centric designs that NLL
  discouraged. Use this skill whenever the user mentions Polonius, NLL
  limitations, borrow-checker workarounds, defensive clones, double map
  lookups, get-or-insert helpers, lending iterators, reducing clone counts,
  or asks to audit, simplify, de-clone, or redesign Rust APIs around
  borrowing. Also use it when reviewing Rust code containing
  clone-to-appease-borrowck patterns, entry() calls with cloned keys,
  id/index indirection standing in for references, or clone-modify-writeback
  sequences — even if the user does not name Polonius. Provides two modes
  (workaround retirement; ownership-model evolution), a pattern catalogue
  with lifetime-versus-aliasing discriminators, an API evolution playbook,
  worked examples, and a documentation strategy.
---

# NLL to Polonius migration

Migrate a Rust codebase to Polonius and, where the codebase's stability
posture allows, evolve its internal APIs from the owned-value style NLL
pushed everyone into toward the borrow-centric model Polonius makes
natural. Retire the workarounds, redesign the accommodations, refuse the
rewrites that borrow checking was never the reason for, and document the
result so neither humans nor coding agents regress it.

## Status and framing (read before touching code)

Polonius "alpha" is the location-sensitive borrow-checking analysis on
nightly behind `-Zpolonius=next`. As of mid-2026 it is a Rust project goal
for stabilization, not yet stable. Four facts govern the migration:

1. **Polonius accepts a strict superset of NLL.** Nothing that compiles
   today breaks. There is no porting cost, only a toolchain binding.
2. **NLL shaped architecture, not just local code.** A codebase that is
   clean under NLL is not evidence of nothing to do — it is evidence the
   design bent around NLL before any error could appear. The tells are
   structural: lookups returning owned values or ids instead of
   references, clone-modify-writeback sequences, eager error context,
   clone counts in the hundreds. The deepest value of the migration is
   unbending these, not deleting `contains_key` calls.
3. **Polonius fixes lifetime problems, not aliasing problems.** It relaxes
   how long a loan is considered live, not who may hold borrows
   simultaneously. Aliasing constraints — and the related pressures from
   async, event loops, and thread boundaries — are permanent features of
   Rust, and some owned-value style exists because of *them*.
   Distinguishing NLL residue from these permanent constraints is the
   skill's central judgement call.
4. **Simplified code stops compiling under plain NLL.** Every rewrite
   binds the crate to a Polonius-enabled toolchain. Decide the posture
   first.

The old datalog implementation (`-Zpolonius=legacy`) accepted more exotic
flow-sensitive patterns but has no path to stabilization. Target the alpha
analysis only.

## Choose a mode

**Mode E — model evolution (default for applications, pre-1.0 crates, and
crates whose only API consumers are themselves).** Internal APIs are
malleable; the goal is the better design, and call-site churn is part of
the work, not a cost to minimize. Redesign lookup, caching, traversal, and
error-path APIs around returned borrows; retire the id/clone indirection
they replace.

**Mode R — workaround retirement (for published libraries, MSRV-bound
crates, or code the user marks stable).** Only local rewrites of confirmed
NLL workarounds; API signatures stay fixed; anything requiring signature
change is flagged, not performed.

Ask the user which applies if the repository does not make it obvious
(version numbers below 0.1.0, absence of external dependents, and
`publish = false` all point to mode E). The phases below are shared; mode
determines how phase 3's findings are acted on.

## Workflow

### Phase 1: verify the toolchain

```bash
rustc +nightly --version
RUSTFLAGS="-Zpolonius=next" cargo +nightly check 2>&1 | tail -5
```

No nightly available → prepare-only posture (phase 4b): annotate and
design on paper, rewrite nothing.

### Phase 2: decide the deployment posture

**Adopt now.** Pin nightly in `rust-toolchain.toml` and set
`-Zpolonius=next` in `.cargo/config.toml` under `[build] rustflags`. Use this
for mode E codebases and anything already on nightly.

**Prepare only.** Audit, annotate, and record target designs; execute on
stabilization. Use this for MSRV-bound crates and teams unwilling to pin
nightly.

For "adopt now", also thread the flag into CI and rust-analyzer
(`rust-analyzer.cargo.extraEnv` or the checked-in `.cargo/config.toml`);
otherwise editors show phantom errors on correct code and invite
regression.

### Phase 3: audit — two passes

**3a. Workaround scan.** Run the bundled scanner:

```bash
bash scripts/audit_candidates.sh /path/to/repo
```

Output is suspects, not rewrites. Classify each against
`references/patterns.md` (§5 discriminator, §4 acceptance matrix).

**3b. Design-pressure scan (mode E).** The scanner's later sections
surface structural accommodation: lookup-shaped functions returning owned
values or ids, clone-modify-writeback sequences, clone-count hotspots.
These feed the API evolution playbook in `references/api-evolution.md` —
read it now in mode E. For each hotspot, identify the owning API and ask
the playbook's question: *would the natural borrow-returning design of
this API fail NLL but pass Polonius?* If yes, it is an evolution target.
If it would fail both (aliasing, loop-carried reborrow, borrows across
await), the owned style is load-bearing; record why and move on.

When acceptance is uncertain, compile a minimal reproduction under the
flag. Never assert acceptance from memory; the alpha's boundary is
documented in `references/patterns.md` §4 but the compiler is the oracle.

### Phase 4: execute

**Local rewrites (both modes):** apply the before/after forms in
`references/patterns.md`. **API evolution (mode E):** follow the
sequencing guidance in `references/api-evolution.md` — leaf helpers first,
then let call-site simplification cascade outward; one API per commit so
test failures localize.

After each change:

1. `RUSTFLAGS="-Zpolonius=next" cargo +nightly check` — must pass.
2. `cargo +nightly check` without the flag — the outcome *classifies* the
   change for documentation: failure means the design genuinely exploits
   Polonius (tag `POLONIUS(...)`); success means it was reachable under
   NLL all along (keep it, but document without the toolchain caveat, and
   note that the old form was habit rather than necessity).
3. Full test suite. These changes remove work; behaviour must be
   identical. A test that needs "updating" is a defect signal, with one
   exception: tests that asserted on clone-dependent identities
   (pointer/address comparisons, clone counters) legitimately change.
4. Tag the site per `references/documentation.md`.

### Phase 4b: annotate (prepare-only posture)

No rewrites. Tag candidates in place:

```rust
// POLONIUS-CANDIDATE(case-3): single-lookup get-or-insert once
// -Zpolonius=next stabilizes. Verified accepted on nightly 2026-07.
```

For mode-E evolution targets, additionally record the target signature and
rationale in the tracking document — the design work is toolchain-
independent and worth doing now even when the rewrite must wait.

### Phase 5: document

Follow `references/documentation.md`: toolchain requirement in
README/CONTRIBUTING, site tags, the tracking document, and — most
important — the CLAUDE.md/AGENTS.md block that stops coding agents from
"fixing" borrow-centric code back into defensive form or padding new code
with clones out of NLL-era habit.

## Bundled resources

- `references/patterns.md` — local pattern catalogue, discriminators,
  acceptance matrix. Read during phase 3a classification.
- `references/api-evolution.md` — target API shapes, permanent-constraint
  counterlist, migration sequencing. Read during phase 3b in mode E.
- `references/worked-examples.md` — audit and evolution transcripts from
  five production codebases. Read before the first classification pass.
- `references/documentation.md` — documentation and agent-guidance
  strategy. Read during phase 5.
- `scripts/audit_candidates.sh` — heuristic scanner for both audit
  passes. Execute without reading unless it needs adaptation.
