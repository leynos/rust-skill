---
name: nll-to-polonius
description: >-
  Audit and migrate a Rust codebase for Polonius Alpha, enabled by default on
  current nightly and selectable explicitly with -Zpolonius=next. Evolve
  owned-value internal APIs into the reference-returning, borrow-centric
  designs that NLL discouraged. Use this skill whenever the user asks to
  adopt Polonius, retire NLL limitations, audit borrow-checker workarounds,
  reduce defensive clones, replace double map lookups or get-or-insert
  helpers, enable lending iterators, or redesign Rust APIs around borrowing.
  Also use it when reviewing clone-to-appease-borrowck patterns, entry() calls
  with cloned keys, id/index indirection standing in for references, or
  clone-modify-writeback sequences. Provides two modes (workaround retirement;
  ownership-model evolution), a pattern catalogue with
  lifetime-versus-aliasing discriminators, an API evolution playbook, worked
  examples, and a documentation strategy.
---

# NLL to Polonius migration

Migrate a Rust codebase to Polonius Alpha and, where the codebase's stability
posture allows, evolve its internal APIs from the owned-value style NLL pushed
everyone into toward the borrow-centric model Alpha makes natural. Retire the
workarounds, redesign the accommodations, refuse the rewrites that borrow
checking was never the reason for, and document the result so neither humans
nor coding agents regress it.

## Status and framing (read before touching code)

As of 4 August 2026, current Rust nightly enables Polonius Alpha by default in
preparation for stabilization. Nightly can opt back into NLL with
`-Zpolonius=off`; `-Zpolonius=next` still explicitly selects Alpha and is
useful for older pinned nightlies or deliberate comparison. Stable and beta
remain on NLL at the time of this August 2026 refresh.

Read the router's shared
[Polonius Alpha project posture](../rust-router/references/polonius-alpha.md)
reference before changing toolchain configuration. Four facts govern the
migration:

1. **Polonius Alpha accepts a strict superset of NLL.** Borrowing forms that
   compile under NLL remain accepted.
2. **NLL shaped architecture, not just local code.** A codebase that is clean
   under NLL is not evidence of nothing to do; it is evidence the design may
   have bent around NLL before any error could appear. The tells are
   structural: lookups returning owned values or ids instead of references,
   clone-modify-writeback sequences, eager error context, and clone counts in
   the hundreds. The deepest value of the migration is unbending these, not
   merely deleting `contains_key` calls.
3. **Alpha fixes lifetime problems, not aliasing problems.** It improves
   flow-sensitive reasoning about outlives relationships, not who may hold
   simultaneous borrows. Aliasing constraints, suspension points, event loops,
   and thread boundaries remain permanent features of Rust. Distinguishing NLL
   residue from these constraints is the skill's central judgement call.
4. **Borrow-centric rewrites require a compiler posture that accepts Alpha.**
   Current nightly does so by default. Omitting `-Zpolonius=next` is therefore
   no longer an NLL control; use `-Zpolonius=off` when classifying a rewrite.

The old datalog implementation (`-Zpolonius=legacy`) accepts some more exotic
flow-sensitive patterns but is not the stabilization target. Do not adopt it
as an intermediate production posture.

## Choose a mode

**Mode E: model evolution** (default for applications, pre-1.0 crates, and
crates whose only API consumers are themselves). Internal APIs are malleable;
the goal is the better design, and call-site churn is part of the work, not a
cost to minimize. Redesign lookup, caching, traversal, and error-path APIs
around returned borrows; retire the id/clone indirection they replace.

**Mode R: workaround retirement** (for published libraries, MSRV-bound crates,
or code the user marks stable). Only local rewrites of confirmed NLL
workarounds; API signatures stay fixed; anything requiring signature change is
flagged, not performed.

Ask which applies if the repository does not make it obvious. Version numbers
below 0.1.0, absence of external dependants, and `publish = false` all point to
mode E. The phases below are shared; the mode determines how phase 3's findings
are acted on.

## Workflow

### Phase 1: establish the checker posture

Inspect the toolchain and flags as described in the shared router reference.
For a project pinned to a current nightly, the useful comparison is:

```bash
rustc --version
cargo check
RUSTFLAGS="${RUSTFLAGS:+$RUSTFLAGS }-Zpolonius=off" cargo check
```

The first `cargo check` exercises the project's configured posture. The second
is the NLL control. Preserve any project-specific flags when constructing the
control command.

For an older pinned nightly that supports Alpha but predates the default, an
explicit `-Zpolonius=next` run may be required. If the compiler posture remains
ambiguous, use the shared reference's compile canary.

No Alpha-capable compiler available means prepare-only posture (phase 4b):
annotate and design on paper, but rewrite nothing.

### Phase 2: decide the deployment posture

**Adopt now.** Pin an Alpha-capable current nightly in `rust-toolchain.toml`.
Current nightlies need no `-Zpolonius=next` flag merely to enable Alpha. Keep or
add the explicit flag only when supporting an older pinned nightly or when the
project deliberately wants checker selection written into configuration.

**Prepare only.** Audit, annotate, and record target designs; execute on
stabilization. Use this for MSRV-bound crates and teams unwilling to pin
nightly.

For "adopt now", ensure CI and rust-analyzer use the same pinned toolchain and
Cargo configuration. A current nightly default needs no special
rust-analyzer environment variable. If the project carries an explicit
`next`, `off`, or `legacy` flag, keep that selection in checked-in Cargo
configuration or the editor's Cargo environment so command-line and editor
diagnostics agree.

### Phase 3: audit in two passes

**3a. Workaround scan.** Run the bundled scanner:

```bash
bash scripts/audit_candidates.sh /path/to/repo
```

Output is suspects, not rewrites. Classify each against
`references/patterns.md` (§5 discriminator, §4 acceptance matrix).

**3b. Design-pressure scan (mode E).** The scanner's later sections surface
structural accommodation: lookup-shaped functions returning owned values or
ids, clone-modify-writeback sequences, and clone-count hotspots. These feed
the API evolution playbook in `references/api-evolution.md`; read it now in
mode E. For each hotspot, identify the owning API and ask the playbook's
question: *would the natural borrow-returning design of this API fail NLL but
pass Alpha?* If yes, it is an evolution target. If it would fail both
(aliasing, loop-carried reborrow, borrows across await), the owned style is
load-bearing; record why and move on.

When acceptance is uncertain, compile a minimal reproduction under the
project's Alpha posture and under the explicit NLL control. Never assert
acceptance from memory; `references/patterns.md` documents the current
boundary, but the compiler is the oracle.

### Phase 4: execute

**Local rewrites (both modes):** apply the before/after forms in
`references/patterns.md`. **API evolution (mode E):** follow the sequencing
guidance in `references/api-evolution.md`: leaf helpers first, then let
call-site simplification cascade outward. Keep one API per commit so failures
localize.

After each change:

1. Run `cargo check` with the project's configured Alpha posture. It must pass.
2. Run the NLL control while the preview is nightly-only:

   ```bash
   RUSTFLAGS="${RUSTFLAGS:+$RUSTFLAGS }-Zpolonius=off" cargo check
   ```

   Failure under `off` and success under Alpha means the design genuinely
   exploits Polonius; tag it `POLONIUS(...)`. Success under both means it was
   reachable under NLL all along; keep the simpler form, document it without a
   toolchain caveat, and note that the old form was habit rather than
   necessity.
3. Run the full test suite. These changes remove work; behaviour must be
   identical. A test that needs "updating" is a defect signal, except for tests
   that intentionally asserted clone-dependent identity such as pointer
   comparisons or clone counters.
4. Tag the site per `references/documentation.md`.

### Phase 4b: annotate (prepare-only posture)

Do not rewrite. Tag candidates in place:

```rust
// POLONIUS-CANDIDATE(case-3): use single-lookup get-or-insert once
// Polonius Alpha stabilizes. Verified accepted on nightly 2026-08.
```

For mode-E evolution targets, also record the target signature and rationale
in the tracking document. The design work is toolchain-independent and worth
doing now even when the rewrite must wait.

### Phase 5: document

Follow `references/documentation.md`: toolchain requirement in
README/CONTRIBUTING, site tags, the tracking document, and, most importantly,
the CLAUDE.md/AGENTS.md block that stops coding agents from "fixing"
borrow-centric code back into defensive form or padding new code with clones
out of NLL-era habit.

## Bundled resources

- `../rust-router/references/polonius-alpha.md`: current project-posture
  detection, semantic delta, and the boundary shared by ordinary Rust skills.
- `references/patterns.md`: local pattern catalogue, discriminators, and the
  acceptance matrix. Read during phase 3a classification.
- `references/api-evolution.md`: target API shapes, permanent-constraint
  counterlist, and migration sequencing. Read during phase 3b in mode E.
- `references/worked-examples.md`: audit and evolution transcripts from five
  production codebases. Read before the first classification pass.
- `references/documentation.md`: documentation and agent-guidance strategy.
  Read during phase 5.
- `scripts/audit_candidates.sh`: heuristic scanner for both audit passes.
  Execute without reading unless it needs adaptation.
