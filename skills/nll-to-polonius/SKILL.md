---
name: nll-to-polonius
description: >-
  Evaluate Polonius adoption, audit suspected NLL workarounds, and evolve
  Rust ownership APIs where useful. Use for Polonius migration, defensive
  clones, double lookups, get-or-insert helpers, lending iterators, or
  borrow-centric API reviews. Separate ordinary ownership improvements
  from demonstrated checker-dependent changes using explicit off/next
  comparisons on one pinned nightly. Includes API evolution, semantic
  constraints, reproducible compiler controls, and documentation guidance.
---

# NLL to Polonius migration

Find the best ownership design, then establish whether it needs Polonius.
Retiring a workaround, improving an API, and changing the supported toolchain
are separate decisions. A valid audit can recommend useful refactors and no
compiler migration.

## Status and framing (read before touching code)

Status checked on 2026-09-26: the Rust project's
[tracking issue](https://github.com/rust-lang/rust/issues/160456) records
Polonius Alpha enabled by default starting with `nightly-2026-08-06`, ahead
of stabilization. `-Zpolonius=next` explicitly selects Alpha and
`-Zpolonius=off` selects the NLL control on a supporting nightly. Recheck
upstream status and the exact compiler before relying on these switches.
A moving channel name is not evidence of checker behaviour.

Four rules govern the work:

1. **An omitted flag is not an NLL control.** Defaults change, and Cargo
   configuration or environment variables may still select a checker. Use
   explicit `off` and `next` on the same pinned compiler, holding other
   inputs fixed. Read [the verification protocol](references/verification.md).
2. **A clone is a lead, not a diagnosis.** Owned results, IDs, snapshots,
   and reference counts may implement identity, lock release, transactional
   staging, or asynchronous hand-off. Compiling under NLL does not prove
   that a design bent around NLL; clone counts do not establish causation.
3. **Improved borrow analysis does not change ownership contracts.**
   Polonius may accept a loan that only escapes on another path. It does
   not permit overlapping exclusive borrows, extend an owner's lifetime,
   or change `Send`, `Sync`, dyn compatibility, or serialization. Borrowing
   across `.await` and scoped threads can already work under NLL.
4. **Not every improvement needs a new checker.** Test the proposed
   replacement, not merely the existing code. Accept/accept is ordinary
   refactoring; a relevant NLL borrow error plus Alpha acceptance is a
   checker-dependent candidate. Neither establishes a runtime speedup.
   Do not promise that an experimental compiler has no regressions.

Target Alpha, not the legacy datalog implementation. A result obtained with
`-Zpolonius=legacy` does not establish acceptance under `next`.

## Choose API scope independently of compiler policy

**Mode E: model evolution.** Default for private/internal APIs, applications,
and pre-1.0 APIs. Change signatures and all relevant callers together where
that improves the design. Returned borrows are one option; consuming an owned
value, splitting fields, retaining a shared handle, or moving instead of
cloning may be better. Read [the API playbook](references/api-evolution.md).

**Mode R: workaround retirement.** Use where a released, externally consumed
API or explicit maintainer instruction constrains signature changes. Preserve
that contract and report broader redesigns separately. An MSRV constrains
compiler use; it does not by itself freeze private API signatures.

Do not retain obsolete private APIs or add dual production implementations
merely to conduct the comparison. Comparison fixtures are experimental
controls, not a promise of maintained compatibility products. Preserve any
actual released support contract separately from the experimental design.

Neither Mode E, `publish = false`, nor an existing nightly build for a
helper tool authorizes changing the crate's compiler support contract.
When policy is unclear, audit without changing it and record the assumption.

## Workflow

### Phase 1: establish the actual build

Inspect the crate's toolchain, MSRV, features, targets, CI, release and
consumer builds, editor configuration, and compiler wrappers. Distinguish
building a helper on nightly from building the product on nightly.

Record the source revision, `rustc +nightly-YYYY-MM-DD -Vv`, Cargo version,
edition, dependency lockfile, target, and effective flags. Inspect project,
ancestor, and Cargo-home configuration as well as `RUSTFLAGS`,
`CARGO_ENCODED_RUSTFLAGS`, target-specific flags, and relevant rustdoc flags.
Do not classify an infrastructure failure as a borrow-checker rejection.

### Phase 2: choose a provisional deployment posture

**Retain support.** Default while assessing benefit. Apply independently
justified refactors that pass the existing support gates. Keep genuine
checker-dependent alternatives as isolated probes or documented proposals.
This does not require retaining obsolete private APIs in production.

**Evaluate adoption.** Use when the maintainer requests an experiment or a
specific candidate warrants one. Set a bounded effort budget, representative
specimen, and acceptance/rejection criteria. Change the compiler support
contract only after evidence and an explicit adoption decision.

**Prepare only.** When execution is unavailable, distinguish source-review
hypotheses from verified results. Do not claim a migration or invent a
compiler run, acceptance result, or verification date.

### Phase 3: audit in two passes

From the installed skill directory, run:

```bash
bash scripts/audit_candidates.sh /path/to/repo
```

**3a. Local candidates.** Treat scanner output as suspects. Use
[patterns.md](references/patterns.md) to identify the exact escaping loan
and the semantic purpose of the current ownership. Audit caller needs.

**3b. Owning APIs (Mode E).** Compare the proposed interface with the
strongest compatible alternative, not an artificially clone-heavy baseline.
Consider standard `Entry`/`Option` APIs, field splitting, consuming signatures,
and moving the final owned value. Do not invent lazy creation, mutable
access, or new consumers merely to manufacture a Polonius use case.

A failure under both checkers rejects that formulation, not every possible
borrowed design. Narrow the conflict before deciding ownership must remain.

### Phase 4: verify and execute one change at a time

Follow [verification.md](references/verification.md) before applying tags:

1. Compile the baseline and replacement under explicit `off` and `next`
   on one pinned nightly. Hold the solver fixed. If a new-solver benefit
   is claimed, run the independent two-by-two checker/solver matrix.
2. Preserve full commands, compiler identities, statuses, and diagnostics.
   Attribute failure only to a relevant borrow error in the replacement.
   Existing Alpha-only code elsewhere requires an isolated reproducer;
   a failing whole-crate NLL check cannot classify every later edit.
3. Run the actual stable/MSRV support gates separately when promised.
   Nightly with `off` is not a stable compiler support test.
4. For accepted changes, run the full behavioural tests and relevant
   lint, docs/doctest, packaging, consumer, and editor checks. Preserve
   hit/miss behaviour, fallible initialization, retry, error precedence,
   lock duration, snapshot semantics, cancellation, and drop timing.
   Do not waive a test merely because it asserts identity or clone counts;
   establish whether that observation belongs to the contract.
5. Measure claimed performance changes, including miss-path costs and
   compile-time/tooling costs. Acceptance and fewer source-level clones
   are not measurements.

For adoption, pin the compiler and align CI, editor, docs, release, and
consumer builds. Alpha-default nightlies need no extra flag merely to enable
Alpha; explicit selection remains useful for attribution. A dependency's
`.cargo/config.toml` does not automatically configure its consumers.

### Phase 5: document evidence and limits

Use [documentation.md](references/documentation.md). Separate confirmed
checker-dependent sites, checker-independent improvements, untested
hypotheses, and retained ownership with its concrete reason. Tag only what
was demonstrated. Do not describe stabilization of an unstable flag as a
promised language feature or infer a stabilization date.

## Bundled resources

- [Verification protocol](references/verification.md): explicit controls,
  Cargo flag precedence, solver isolation, and evidence requirements.
- [Pattern catalogue](references/patterns.md): local borrowing shapes and
  the lifetime-versus-aliasing discriminator.
- [API evolution playbook](references/api-evolution.md): compatible
  alternatives, ownership contracts, and sequencing.
- [Worked examples](references/worked-examples.md): corrected historical
  interpretations and the pinned Peregrine design-PR evidence.
- [Documentation strategy](references/documentation.md): support policy,
  evidence-backed tags, and agent guidance.
- `scripts/audit_candidates.sh`: heuristic scanner, not an acceptance test.
