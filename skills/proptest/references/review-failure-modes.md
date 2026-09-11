# Proptest review failure modes

What reviewers actually flagged on property tests across the estate
(550 findings; method and counts in
`docs/verification-review-failure-modes.md`). Use it as a pre-submission
checklist. The categories are ordered by frequency.

## 1. The property is missing (197 findings)

The trigger rule reviewers apply, quoted in at least ten repositories:

> Property tests, using proptest (Rust), Hypothesis (Python) or fast-check
> (TypeScript), or a bounded model checker, such as Kani (Rust) or
> CrossHair (Python), should be recommended when the change introduces an
> invariant over a range of inputs, states, orderings, or transitions.

Typical wording of the CodeRabbit "Testing (Property / Proof)" row:
"relies solely on concrete example tests", "proptest available but
unused; only 2 hardcoded test cases", "`proptest` was already available
in `Cargo.toml`, and no new property test appears in the changed files".
The row is a warning, it recurs verbatim each round until satisfied, and
it can regress from Passed to Warning inside one PR as the invariant
surface grows.

Answers reviewers accept:

- the property test, in the same PR;
- a tracked issue, when the human reviewer's standing instruction allows
  ("Where a change is out of scope for this PR, propose a GitHub issue
  unless one exists already");
- a written scope statement in the PR body, ExecPlan, or developers'
  guide explaining why the invariant is bounded and deterministic enough
  for enumerated cases ("exhaustive hand-written matrices are appropriate
  only when the invariant input space is small and finite enough to
  enumerate reliably"). An unsolicited property test where an ExecPlan
  decided against one is also flagged.

Answers reviewers reject: silence; claiming coverage that does not exist
("PR claims proptest coverage for isolation marks but none exists");
arguing enumerability for a space that is not exhaustively run each time.

## 2. Weak or unreachable strategies (86)

- A generated binding that never reaches the assertion ("it always sends
  a one-byte patch, so it does not exercise the advertised
  `1..=MAX_PATCH_BYTES` range").
- Bounds that cannot hit the limit under test (4 URIs and 64 operations
  against a queue whose limits sit far higher).
- Happy-path generators: reviewers expect a generator per documented
  input variant and per state-machine transition ("single-quoted titles,
  angle-bracketed URLs, indentation (0-3), escaped content, and state
  machine transitions not property-tested").
- Generators that emit impossible input, so the property fails on invalid
  samples: exclude the fence delimiter from body strategies; prefix path
  segments so `[a-z]{1,5}` cannot produce Windows device names such as
  `CON`. Transform the generator; do not `prop_filter` ("adds rejection
  noise and can reduce test efficiency").
- Partial grammars (language-region only, not full BCP 47).
- One-directional assertions: `if flag { prop_assert!(..) }` never
  constrains the false branch; use `prop_assert_eq!(actual, expected)`.
- Enum strategies hardcoding a subset instead of deriving from the
  canonical `ALL` constant.
- Off-by-one exclusive ranges narrowing the space below the documented
  bound.
- `prop::sample::select` over a small fixed set that would be better as
  deterministic `rstest` cases.

## 3. Tautological or reimplemented oracles (22)

- Assertions that do not depend on the generated value ("only asserts
  the constant `flock_pos < key_generation`, which does not vary with the
  selected `exit_pos`").
- Facts the fixture guarantees by construction (cycle closure, length
  relationship).
- `max_degree >= avg_degree`.
- Properties encoding current behaviour rather than the intended
  invariant (a SHA validator that accepted prefixes, and a property that
  accepted "prefix lengths from 7 through 40").
- Re-deriving sort-and-compose logic instead of calling the production
  function; reviewers require "an independent traversal oracle" or "a
  trusted clamp reference".
- Oracle helpers one token away from production (`source.len()` versus
  `source.len().max(1)`; `trim()` hiding CRLF handling).
- A stubbed operation branch (`Ok(false)` for Delete) so an operation
  class is never exercised.

## 4. `prop_assume!`, filters, and early returns (9, but sharp)

- `prop_assume!` is a precondition. On the output it is a vacuous pass;
  it must run before the function under test.
- It must not exclude cases the domain code must handle (duplicates);
  it is for structurally invalid generator output only, and only when
  rare.
- Environment preconditions ("is this dependency installed?") go in one
  guard outside `proptest!`; inside the loop they reject every case and
  abort with "Too many global rejects".
- Assumptions must be side-effect-free; never gate on a mutating call.
- Silent early returns hide rejection; use `prop_assume!` so the runner
  counts it.
- A filter for a case the strategy structurally cannot produce is dead
  code.

## 5. Assertions and panics in the body (18)

The `.unwrap()` versus `.expect()` policy differs per repository:

- `.expect("context")` preferred in test bodies: axinite, mxd,
  wireframe.
- `clippy::expect_used = "deny"` workspace-wide, applied to proptest
  bodies: netsuke.
- Both denied, with a named panic-boundary trait for `prop_compose!`
  closures, which cannot propagate errors: tei-rapporteur.
- `unwrap_or_else(|| panic!(..))` so formatting happens only on the
  failure path: zamburak.

Read the workspace `[lints]` table first. Beyond that:

- `||` inside `prop_assert!` accepting two observed behaviours "permits
  the wrapper to drop the semantic space"; require the one correct form.
- Test-support helpers that lock or set up propagate `TestCaseError`
  rather than panicking.
- A body that calls the function and asserts nothing is a does-not-panic
  smoke test; if an invariant is known, assert it.
- Conditionals with more than two branches move into a predicate or
  classifier helper outside the `proptest!` block.
- `expect_err` or `prop_assert!(matches!(..))` over `unwrap_err`.

## 6. Configuration, tiering, determinism (36 across categories)

- `ProptestConfig { cases: 1, .. }` "reduces property-based testing to a
  parameterised test with a single random parameter" and signals
  unresettable global state; add a test-only reset hook.
- Documented budgets must be enforced by an explicit
  `#![proptest_config(..)]`, and large budgets must come from an
  environment variable so CI can tier them.
- `fork` and `cases` multiply; forking every case blew a 600 s CI
  timeout. A cap only works if nothing downstream re-reads
  `PROPTEST_CASES` and overrides it.
- No wall-clock assertions inside a property; use a fuel budget and a
  separate watchdog.
- `HashMap`'s `RandomState` is outside proptest's seed: "shrinking
  silently discards valid candidates and committed regression seeds are
  decorative". Use a seeded or ordered map for anything the property
  observes.
- `ProptestConfig::default()` is not deterministic; do not say it is.
  When standardizing a fixed seed, keep `PROPTEST_RNG_SEED` overridable.
- Properties that mutate the process environment take the environment
  lock inside the strategy helper, never across an iteration boundary.
- Properties that rely on one process per test are not portable between
  `cargo test` and `cargo nextest`.
- Unnecessary `#[cfg(windows)]` gating means other platforms never run a
  portable invariant.
- Thread config newtypes (`TestCases`, `ShrinkIterations`) through helpers
  rather than unwrapping to raw integers, and validate them consistently.

## 7. Regression files (6)

- Persistence is keyed to the declaring source file: rename the
  `.proptest-regressions` file when the source moves.
- A source both `#[path]`-included and discoverable as its own target runs
  twice with two regression paths, orphaning seeds.
- Mutation testing generates seeds from injected defects: disable
  persistence during mutation runs; neither commit those seeds nor
  blanket-ignore the directory.

## 8. Layout, lint, packaging (34 across categories)

- The estate's 400-line file cap is the most common reason a proptest
  addition triggers a mid-review refactor. Start in a sibling module:
  `tests_proptest.rs` plus `tests_proptest_strategies.rs`, or
  `prop_tests.rs` per module, following the repository's convention
  (some repositories keep inline blocks so coverage tooling sees them).
- Every module, including strategy modules, begins with a `//!` comment.
- `proptest!` functions need `#[test]` inside the block; without it the
  block compiles, runs nothing, and passes.
- `Box::leak` per case leaks per case; use a static sample pool.
- An unused `proptest` dev-dependency is read as evidence of a gap.
- Declare `proptest` once in `[workspace.dependencies]` and opt in with
  `proptest = { workspace = true }`; pin to a current explicit version
  where the repository requires exact pins.
- Large deterministic fixtures go in an external file via `include_str!`.
- Strategy chains and bodies are subject to the same Clippy thresholds
  as production code (cognitive complexity ≤ 9, args ≤ 4, nesting ≤ 4).
- Property tests reference the same named constants as production, not
  re-typed literals.
