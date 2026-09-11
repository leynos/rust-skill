# Kani review failure modes

What reviewers actually flagged on Kani harnesses across the estate
(159 findings; see `docs/verification-review-failure-modes.md` for the
method and counts). Use this as a pre-submission checklist.

## Vacuous harnesses (the most common quality finding)

- **Placeholder proofs.** A `kani::assert(true)` scaffold left in to
  validate `cargo kani --list` must be replaced before merge.
- **Harness builds the expected value directly.** A harness that
  constructs the error it expects instead of calling the production
  function under a symbolic input proves the harness.
- **Hand-written mirror.** Calling a re-implementation of the production
  function, or asserting against a hand-rolled model helper, proves the
  model is self-consistent. Drive the production function; if a mirror is
  unavoidable, add an explicit equivalence proof or exhaustive
  equivalence tests, and record why.
- **Swallowed failure paths.** `if let Ok(x) = f(...) { assert... }`
  skips verification on `Err`; `opt.unwrap_or(false)` before
  `kani::assert(!x, ..)` passes on `None`. Assert `Ok`/`Some` first, and
  on an unexpected arm fail loudly: `kani::assert(false, "reason")`.
- **Global assumptions.** `kani::assume(false)` or a blanket
  `kani::assume` inside production code prunes every path for every
  harness, present and future. State preconditions at each harness's
  call site through typed symbolic inputs.
- **Pointer-identity selection.** Choosing an assertion by comparing
  `&'static str` addresses relies on unspecified string-literal
  interning, so it may select the wrong assertion or none at all; with
  an `assume(false)` fallback the harness becomes vacuous.
- **Missing `kani::cover!`.** Every branch the harness claims to reach
  needs a `cover!`; a harness that never reaches the interesting branch
  is green and worthless. `theoremc` enforces a non-empty witness list at
  schema level for this reason.
- **Assertions that cannot fail.** Bounds-checking a type that cannot
  violate the bound gives false assurance; exercise a data-dependent
  branch.
- **Inclusion without exclusion.** "Every output traces to an input" is
  not "no output lacks an input"; prove both directions.
- **Claims wider than the inputs.** A harness documented as covering all
  levels with `level` hardcoded to `0` overstates coverage.
- **Proving misuse harmless.** If a proof only shows an invalid argument
  combination is currently benign, narrow the API so the combination is
  statically impossible instead.

## Model-mirror drift

- Prefer production types over Kani-only twins; `chutoro` deleted its
  `KaniCommitUpdate` layer for this reason.
- One driver for proptest and Kani under `#[cfg(any(test, kani))]`, so
  a signature change cannot desynchronize them.
- Harness-side invariant checks call the production invariant helper.
- Kani-only helpers assume the same preconditions production enforces;
  a missing node must not silently become an empty state.
- Compressed proof-seam views must preserve exact production equality
  semantics, or the harness proves invariants over unreachable states.
- A refactor that changes loop or traversal shape can blow the unwind
  bound; re-run the harness and recompute bounds in the same change.
- When a parallel Kani-only reimplementation is the right call (to avoid
  collection drop-path unwinding), record the state-explosion evidence so
  "reduce duplication" can be declined with numbers.

## Solver cliffs

- Collections and strings dominate the proof budget: real `HashMap`,
  serde, hashing, `Utf8PathBuf`, and `BTreeMap` internals are lowered
  before your invariant is reached. Prefer fixed-size arrays, an explicit
  degree cap, or a bounded array with an O(n²) linear scan in place of a
  `HashSet`.
- Extract a generic kernel and prove it over a minimal symbolic type
  (`u8`) with a thin adapter harness for the production wrapper; this
  turned a proof that exhausted 8 GiB at N=3 into 7.6 s.
- Nested loops need N² unwind, not N. Recompute after any refactor.
- Bounded inputs can hide branches (overflow handling) that only fire
  outside the bound; add a smoke harness or document the gap.
- Bind unwind literals, array capacities, and production constants with
  `const` assertions; where `#[kani::unwind]` forbids it, document the
  coupling.
- Code-health refactors (closures, generic wrappers) can push CBMC past
  the SAT solver's variable-index limit; validate against `make
  kani-full` in isolation before accepting one.
- When a requested harness is intractable, measure it (record the
  timeout and aborted-path count), substitute an equivalence or unit-test
  proxy, open a tracked issue, and say so in the PR. Reviewers accept a
  measurement; they do not accept "too hard".

## `cfg(kani)` is a different build

The normal gates do not see harness code. Expect the following at review
time unless you check them yourself:

- Unused imports and dead code under `cfg(kani)` survive `-D warnings`;
  only a Kani build (or a lint pass built with `--cfg kani`) finds them.
- Clippy's allow-`expect`-in-tests exemption does not apply; use `match`
  and early return, or the repository's approved panic boundary.
- Complexity thresholds (cognitive complexity, function length, argument
  count, nesting) and CodeScene gates apply to harness helpers; factor
  symbolic-input setup into one helper and group parameters early.
- A call into a `cfg(test)`-only helper from code that also compiles
  under `cfg(kani)` breaks every harness in the crate.
- `#[allow(dead_code)]` as a gating workaround hides a real configuration
  mismatch; use `#[expect(lint, reason = "...")]` scoped to the item, and
  delete wrappers nothing calls.
- `trybuild` fixtures that include a `cfg(kani)` module scope
  `#[expect(unexpected_cfgs, reason = "...")]` to the `mod` line.
- `cargo-mutants` ignores the cfg; exclude harness modules or their
  survivors are noise.
- Kani bundles its own nightly. A `const fn` or borrow that compiles on
  the workspace toolchain can fail under Kani; setting `RUSTUP_TOOLCHAIN`
  does not upgrade Kani and can produce a mismatched driver and sysroot.
  Kani 0.67.0's nightly predates Polonius by default.
- Kani cannot model FFI into an embedded interpreter, real syscalls,
  async I/O boundaries, or (on some versions) default `HashSet` entropy.
  Fail the gate closed and track the blocker, refactor to a pure state
  machine over an event enum, or use proptest.

## Documentation that reviewers cross-check

- Harness inventory table updated in the same PR.
- No claim that a gate "succeeded" where the same document records it
  failing; checkbox lists agree with narrative.
- Unwind values and bounds stated in one place, or updated everywhere in
  one commit.
- Rustdoc on every Kani-only helper covering the why, not only the what.
- Deliberate simplifications (no path compression) documented so nobody
  "fixes" them into a blow-up.
- Behaviour that differs under `cfg(kani)` (panic versus abort) in the
  public doc comment.
- Makefile snippets in docs use real tabs; docs never invent CLI surface.

## Assertion choice inside harnesses

- `kani::assert(cond, "msg")` for the property; `assert_eq!`/`assert_ne!`
  where both values should appear in the counter-example.
- No `.expect()`/`.unwrap()` in setup; a panicking setup path defeats the
  harness rather than failing the obligation.
- Validate indices in helpers defensively; an unguarded index panic masks
  the intended verification.
- Prefer `const` assertions or `kani::assume` over runtime early returns.
