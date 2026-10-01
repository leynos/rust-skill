# Documentation strategy

Document the ownership decision and its evidence, not an assumed victory for
one checker. Separate a source-review proposal, a compiler result, a tested
behavioural change, and a measured performance result. Read
[verification.md](verification.md) before writing acceptance claims.

## 1. State the actual support contract

For an adopted Alpha-dependent design, describe the exact pinned compiler,
effective configuration, affected sites, and consumer build requirements.
Explain that Alpha-default nightlies do not need `next` merely to enable it,
while explicit `off`/`next` selection remains necessary for attribution.
Do not imply that an unflagged nightly selects NLL.

For a compatible cleanup, do not invent a nightly requirement. For an
unexecuted experiment, state that support remains unchanged and identify the
missing evidence. Nightly with `off` does not prove stable/MSRV support.

A dependency's Cargo configuration does not automatically configure its
consumers. Test an external consumer, packaging, docs/doctests, CI, and editor
builds before declaring support. Stable builds may reject unstable flags
before reaching borrow checking; report the actual failure rather than
promising a particular diagnostic.

## 2. Evidence-backed site tags

Use `POLONIUS(...)` only for a replacement with an observed, relevant NLL
borrow error and Alpha acceptance under controlled inputs. Link it to the
archived command, source, compiler identity, and diagnostic. For example,
adapt this template with real evidence before using it:

```rust
// POLONIUS(case-3): borrowed hit avoids owning the miss-path key.
// Explicit off/next comparison and compiler identity: docs/polonius.md.
```

A proposal without that evidence is a candidate, not a verified result:

```rust
// POLONIUS-CANDIDATE(case-3): proposed early borrowed return.
// Not compiled yet; preserve current support until the experiment resolves.
```

Retained ownership should name a concrete contract:

```rust
// POLONIUS-REFUSED(snapshot): queued work retains its enqueue-time handlers.
// Borrowing the live registry would change that behaviour.
```

Do not attach a Polonius-dependency tag to an accept/accept refactor. Do not
copy a sample date or compiler version into a claim of verification. A failed
rewrite alone does not prove all alternatives fail. Refusal tags record a
reason to preserve a contract, not a ban on every future implementation.

## 3. Tracking document

Keep the inventory small and evidence-oriented. Separate:

- confirmed checker-dependent sites and their best compatible alternatives;
- checker-independent ownership improvements;
- untested or inconclusive candidates;
- retained ownership and its semantic reason.

For each relevant row, record the file/API, source revision, compiler identity,
flags, scope, result, diagnostic, behaviour checks, and any measured costs.
Link full logs rather than replacing them with the last few lines. Record
solver effects independently; use all four cells when claiming a new-solver
benefit. Describe historical results as historical, with immutable links.

Update the support decision separately from the inventory. A compiler
upgrade can invalidate an old rejection or introduce a regression. Rerun the
controls; do not preserve obsolete requirements because a comment says so.

## 4. Agent guidance for an adopted repository

Adapt this block to the repository's real commands and policy:

```markdown
## Borrow checking

Use the pinned project compiler and effective flags documented in
`docs/polonius.md`. Do not change supported toolchains as an incidental cleanup.

- Preserve deliberate borrowed forms and legitimate owned/shared boundaries.
  Neither an old workaround nor a new reference-returning API is automatically
  the best design. Test an alternative before recommending a rewrite.
- Classify a proposed checker-dependent change using explicit `-Zpolonius=off`
  and `-Zpolonius=next` on one pinned nightly, with other inputs fixed.
  Omitting `next` does not select NLL. Audit encoded flags and Cargo config.
- Attribute only relevant borrow diagnostics. An unrelated existing Alpha-only
  site, unsupported flag, or missing dependency cannot classify this edit.
- Field splitting and scoped borrows across await can work under NLL.
  Preserve owner lifetimes, guard scopes, snapshots, failure semantics, and
  task/executor bounds. Polonius does not change those contracts.
- Prefer the best interface for actual callers: borrowing, consuming an owned
  value, moving fields, or retaining a shared handle as appropriate.
- Keep stable/MSRV support checks, behavioural tests, and performance evidence
  distinct from the checker comparison. Record unexecuted checks explicitly.
```

A retain-support repository should additionally state that Alpha-only source
must remain a proposal until adoption is authorized. It may still accept
ordinary ownership improvements that pass its existing support gates.

## 5. Review and changelog

Record a compiler-support change only when one actually occurs. Otherwise,
describe the API/ownership cleanup and its evidence without the toolchain
claim. Do not turn experiment controls into maintained compatibility variants.

Review the strongest compatible design, representative callers, negative
controls, behavioural tests, and performance claims. Identity, clone counters,
drop timing, and callback order may belong to the contract; a changed test
needs an explicit explanation rather than an automatic exemption.

## 6. Editor, documentation, and CI consistency

Align local development, CI, release, consumer, and editor invocations with
the chosen compiler policy. Inspect rustdoc flags independently from rustc
flags. Use verbose compiler commands to check the effective selection where
wrappers or layered configuration create ambiguity. Do not replace required
linker or `cfg` flags with a checker flag and call the resulting build a valid
control. Keep full logs without publishing secrets from the environment.
