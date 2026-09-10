# Verification review failure modes: a compendium

A survey of pull-request review threads and CodeRabbit pre-merge checks
across the Rust and Rust-plus-Python repositories of the `leynos` GitHub
estate, looking for recurring failure modes when implementing `proptest`
property tests, Kani bounded model checking harnesses, and Verus deductive
proofs, and for cases where those artefacts were omitted from the original
change, requested by a reviewer, and then landed before merge.

The compendium exists to drive updates to the `proptest`, `kani`, and
`verus` skills in this catalogue so that an implementer meets the review
bar first time and has an easier on-ramp to each tool. The section
[Implications for the skills](#implications-for-the-skills) records which
findings became which skill changes.

Survey date: 2026-09-10. The canonical tool route assumed throughout is
[`rust-prover-tools`](https://github.com/leynos/rust-prover-tools)
(`prover-tools kani install|check-version`, `prover-tools verus
install|run`).

## Method and corpus

Repositories were taken from the estate inventory
(`~/docs/estate-ecosystems.md`): every row whose toolchain is Rust or a
genuine Rust-plus-Python mix, plus `rust-prover-tools` itself. For each
repository the survey pulled every pull-request review comment, every
issue comment on a pull request (this is where CodeRabbit posts its
walkthrough and pre-merge check tables), and every review body.

| Corpus dimension                    | Count  |
| ----------------------------------- | ------ |
| Repositories                        | 57     |
| Pull requests                       | 9,171  |
| Review (inline) comments            | 86,666 |
| Issue comments on pull requests     | 52,007 |
| PRs with verification keyword hits  | 1,208  |
| Repositories with hits              | 51     |

Keyword matching (proptest, `prop_assert`, `prop_compose`, `prop_assume`,
property-based, Kani, `kani::`, unwind, Verus, `vstd`, `spec fn`,
`proof fn`, bounded model checking, `prover-tools`, formal verification,
shrink) produced one digest per repository. The digests were split into
72 chunks and triaged by a team of agents against a fixed category
vocabulary, with a second lead pass validating coverage against keyword
density and sending thin chunks back for re-reading. The integration
baseline (Makefiles, CI, pins, contract tests, design documents) came from
shallow clones of the ten repositories with the deepest formal-verification
footprint.

| Triage output                                | Count |
| -------------------------------------------- | ----- |
| Findings recorded                            | 851   |
| Pull requests with at least one finding      | 391   |
| Repositories with at least one finding       | 42    |
| Findings tagged proptest                     | 550   |
| Findings tagged Kani                         | 159   |
| Findings tagged Verus                        | 28    |
| Findings tagged prover-tools                 | 21    |
| Findings tagged cross-cutting                | 91    |

Reviewer mix, from the two sets where it was tallied (544 findings):
CodeRabbit inline comments 251, CodeRabbit pre-merge check rows 207,
Sourcery 36, `chatgpt-codex-connector` 14, humans 14. About 30% of
findings carry an unknown resolution because the digest excerpt ends
before the author's reply; those counts are lower bounds.

Caveats worth carrying into any reading of the numbers:

- Verbose reviewers inflate counts. `chutoro`, `netsuke`, `mdtablefix`,
  and `whitaker` dominate because they carry the most verification work
  and the most review rounds, not because they are worse.
- CodeRabbit's "✅ Addressed in commit" auto-marker is unreliable. Three
  independent cases (`whitaker` #235, `axinite` #80, `axinite` #154) were
  marked addressed and then re-opened when the human asked "has this now
  been resolved?" The confirmed omission table below therefore rests on
  commit inspection, not the marker.
- Python Hypothesis findings were excluded even where structurally
  identical; Loom and Stateright were out of scope.

## The standard integration shape

The estate has converged on one shape for Kani and Verus, although not
every repository has reached it. The shape is worth stating because a
large share of review findings are about deviating from it rather than
about the harness or proof itself.

- A committed pin file per tool: `tools/kani/VERSION` (currently `0.67.0`
  everywhere it is pinned) and `tools/verus/VERSION` plus
  `tools/verus/SHA256SUMS`. Pins drift between repositories (`chutoro`
  pins Verus `0.2026.01.30`, `wireframe` `0.2026.05.24`).
- Installation and execution delegated to `prover-tools`, invoked through
  `uv tool run --from git+https://github.com/leynos/rust-prover-tools@<sha>
  prover-tools`, with the commit pinned either inline in the Makefile
  (`netsuke`) or in a `tools/rust-prover-tools/REF` file with a
  `git ls-remote` verification line (`wireframe`). Older adopters
  (`chutoro`, `whitaker`) still vendor `scripts/install-kani.sh`,
  `scripts/run-kani.sh`, and `scripts/run-verus.sh`; the review threads on
  those scripts are a catalogue of what `prover-tools` now handles
  (checksums, toolchain resolution, flag passthrough, exit-status
  propagation).
- `#[cfg(kani)]`-gated harnesses declared via
  `unexpected_cfgs = { level = "warn", check-cfg = ["cfg(kani)"] }`, living
  next to the code they verify (a sibling `kani.rs`, a
  `*_kani_proofs.rs`, or an inline module), never widening the public API
  for proof access. Verus proofs live outside Cargo under `verus/`.
- Two Makefile tiers: a curated smoke `kani` target running named
  harnesses with tight bounds, and an exhaustive `kani-full`; a `verus`
  target over named proof files. Neither is part of `make test`,
  `make lint`, or `make all`.
- CI split into a fast pull-request smoke job with a path filter, a
  concurrency group, and a 20–30 minute timeout, and a nightly full job
  with its own timeout. Kani is deliberately uncached in `chutoro`
  (measured: cold install about 16 s) and cached under a version-keyed
  composite action in `netsuke`.
- Contract tests pinning the shape: `wireframe/tests/formal_tooling.rs`
  asserts that verification recipes delegate through `$(PROVER_TOOLS)`
  and never embed `cargo install`, `cargo kani setup`, `curl`, `unzip`,
  `sha256sum`, or `rustup toolchain install`; `netsuke` has Makefile
  contract tests against a fake `prover-tools`, Python workflow-contract
  tests for job step ordering and cache keys, and
  `tests/kani_mutation_evidence_tests.rs`, which requires every
  `#[kani::proof]` to own a mutation patch under
  `docs/verification/mutations/` or an explicit exemption.
- A developers' guide section with a harness inventory table (name,
  bounds, unwind, what is proved) that must be updated in the same PR as
  any harness change.

For proptest, the convention is lighter: `proptest` is an approved
dependency declared once in `[workspace.dependencies]`, property tests
live in sibling `*_proptests.rs` or `prop_tests.rs` files (driven by the
estate-wide 400-line file cap), and only `chutoro` tiers case counts
through the environment (`PROPTEST_CASES` 250 on pull requests, 25,000
weekly, forked). Nobody in the estate uses `proptest-derive` or
`proptest-state-machine`; `test-strategy` appears only in `chutoro`.

## Failure modes: proptest

Frequency across the three triage sets (550 findings):

| Category                              | Count |
| ------------------------------------- | ----- |
| missing-property                      | 197   |
| weak-or-unreachable-strategy          | 86    |
| verification-omitted-then-requested   | 62    |
| docs-or-comments                      | 53    |
| file-layout-or-naming                 | 23    |
| tautological-or-reimplemented-oracle  | 22    |
| config-misuse                         | 21    |
| assert-or-unwrap-in-body              | 18    |
| runtime-cost-or-tiering               | 15    |
| filter-or-assume-overuse              | 9     |
| dependency pinning or currency        | 6     |
| regression-file-handling              | 6     |
| determinism-or-seed                   | 6     |
| lint-or-fmt-interaction               | 5     |
| doesnt-panic-only, case-count tuning  | 4     |

### P1. The property is missing altogether

The single most common review event is not "your property test is wrong"
but "you introduced an invariant and wrote no property test". The
CodeRabbit pre-merge row "Testing (Property / Proof)" fires with wording
such as "relies solely on concrete example tests", "proptest available but
unused; only 2 hardcoded test cases" (`netsuke` #163), or "`proptest` was
already available in `Cargo.toml`, and no new property test appears in
the changed files" (`mdtablefix` #463). The standing trigger rule, quoted
near-verbatim in at least ten repositories:

> Property tests, using proptest (Rust), Hypothesis (Python) or fast-check
> (TypeScript), or a bounded model checker, such as Kani (Rust) or
> CrossHair (Python), should be recommended when the change introduces an
> invariant over a range of inputs, states, orderings, or transitions.

The converse is enforced too. `ortho-config` and `cuprum` carry "Do not
add Kani, Verus, or property-test tooling unless the change introduces a
substantive invariant across a range of inputs, states, orderings, or
transitions", and `netsuke` #540 recorded a durable learning that
"property-based tests are reserved for domains with genuine combinatorial
state. For small input grammars... use focused deterministic tests".
`rstest-bdd` #686 replaced a `prop::sample::select` over six permutations
with six `rstest` cases. `mdtablefix` #295 passed the check by documenting
why the invariants were "bounded, deterministic ... property testing
unnecessary". `podbot` #99 shows the bot enforcing an ExecPlan decision
against an unsolicited proptest, which had to be removed.

The failure mode, then, is not knowing which side of the line a change
falls on, and not saying so. Reviewers accept either a property test or an
explicit, written scope statement; they do not accept silence. A PR body
that claims property coverage that does not exist is flagged as a
claim-versus-reality mismatch (`spycatcher-harness` #38: "PR claims
proptest coverage for isolation marks but none exists").

### P2. Weak or unreachable strategies

The second cluster is a property whose generator cannot reach the
interesting shape:

- A generated binding that never influences the assertion: "This property
  never uses `size`; it always sends a one-byte patch, so it does not
  exercise the advertised `1..=MAX_PATCH_BYTES` range" (`weaver` #103).
- Bounds that cannot hit the limit under test: a bounded-queue property
  with 4 URIs, 64-byte sources, and 64 operations never reached the
  queue's byte or document limits (`rstest-bdd` #660).
- Happy-path-only generators treated as incomplete: "Proptest omits
  critical invariants: single-quoted/parenthesis titles, angle-bracketed
  URLs, indentation (0-3), escaped content, and state machine transitions
  not property-tested" (`mdtablefix` #294). Reviewers expect one generator
  per documented input variant and per state-machine transition.
- Generators that emit impossible input, so the property fails on invalid
  samples rather than on bugs: exclude the fence delimiter from body
  strategies rather than filtering afterwards (`mdtablefix` #343);
  `[a-z]{1,5}` path segments generated Windows reserved device names such
  as `CON` (`netsuke` #635), fixed by prefixing segments, with
  `prop_filter` explicitly rejected because "it adds rejection noise and
  can reduce test efficiency".
- A partial-syntax strategy: locale properties generated only
  language-region forms, "not full BCP 47 syntax" (`spycatcher-harness`
  #43), so the check regressed from Passed to Warning after the first fix.
- One-directional assertions: `if include_reason { prop_assert!(...) }`
  never constrains the false branch; use `prop_assert_eq!(actual,
  expected)` (`rstest-bdd` #529).
- Enum strategies hardcoding a subset instead of deriving from the
  canonical `ALL` constant (`stilyagi`).
- Off-by-one exclusive ranges that silently narrow the tested space below
  the documented bound (`repovec-appliance`).

### P3. Tautological or reimplemented oracles

- An assertion that does not depend on the generated value: "it selects
  `exit_pos` but only asserts the constant `flock_pos < key_generation`,
  which does not vary with the selected `exit_pos`" (`repovec-appliance`
  #37).
- Four `proptest!` cases re-asserting facts the fixture guaranteed by
  construction: "Property tests assert tautologies about test fixture
  construction (cycle closure, length relationship, empty
  missing_dependencies) guaranteed by the test code itself" (`netsuke`
  #334). The block was deleted.
- `max_degree >= avg_degree`, true by definition of a maximum (`chutoro`
  #79).
- A property that encodes the current (buggy) behaviour: `validate_git_sha`
  accepted SHA prefixes and the property accepted "prefix lengths from 7
  through 40" (`whitaker` #272). Derive properties from the desired
  invariant, never from the implementation.
- Re-deriving the sort-and-compose logic instead of calling the
  production function (`rstest-bdd` #492). Reviewers require "an
  independent traversal oracle" or "a trusted clamp reference".
- Oracle helpers that drift from production by one token: "allocates HNSW
  with `source.len()` but `ClusteringSession::new` uses
  `source.len().max(1)`" (`chutoro` #128); `trim()` in an oracle hiding
  CRLF handling (`netsuke` #565).
- A mutation property whose Delete branch was stubbed to `Ok(false)`, so
  deletion was never exercised (`chutoro` #45).

### P4. `prop_assume!`, filters, and early returns

- `prop_assume!` used as a postcondition: "All three original
  postcondition `prop_assume!` calls have been replaced" (`mdtablefix`
  #298). Assumptions must run before the function under test; anything
  about the output is `prop_assert!`.
- `prop_assume!` excluding cases the code must handle, such as duplicate
  values (`repovec-appliance` #23), recorded as a project-wide learning:
  filters are for structurally invalid generator output only.
- Environment preconditions inside the sampling loop: gating a property on
  `msgspec` availability rejected all 1,024 cases and aborted with "Too
  many global rejects" (`tei-rapporteur` #86). Check the environment once,
  outside `proptest!`.
- Side-effecting assumptions: never gate on a command or mutating function
  when a pure query exists (`tei-rapporteur`).
- Silent early returns instead of `prop_assume!`: a property that
  generated mostly nonexistent paths took the `Err` branch and returned
  `Ok(())` without asserting (`netsuke` #329); Sourcery asked for
  `prop_assume!` so the rejection rate is visible (`chutoro` #10).
- Dead filters: a fixed-sample strategy that structurally excludes a case
  makes any `prop_assume!` for that case dead code (`repovec-appliance`).

### P5. Assertion and panic discipline inside the body

- `.unwrap()` versus `.expect()` is repository policy, and the policies
  differ. `axinite`, `mxd`, and `wireframe` want `.expect("context")`
  inside `proptest!` so a shrunk failure carries a message. `netsuke` sets
  `clippy::expect_used = "deny"` workspace-wide and invokes it against
  proptest bodies. `tei-rapporteur` denies both, which forced a documented
  `ExpectValid` panic-boundary trait for `prop_compose!` closures
  (#149) because they cannot propagate errors. `rstest-bdd` prefers
  `expect_err` or `prop_assert*`. `zamburak` prefers
  `unwrap_or_else(|| panic!(...))` over `expect(&format!(...))` so
  formatting happens only on the failure path. Read the workspace lint
  table before writing the first body.
- Disjunctive assertions hide bugs: an `||` inside `prop_assert!` that
  accepts two observed behaviours "permits the wrapper to drop the
  semantic space" (`mdtablefix` #313).
- Test-support helpers that lock or set up must propagate failure as
  `TestCaseError`, not panic (`chutoro`).
- A `proptest!` body that calls the function and asserts nothing is a
  does-not-panic smoke test; if an invariant is known, assert it
  (`mdtablefix`).
- Branching rule: bodies with an `if / else if / else` chain must extract a
  predicate or classifier helper (`actix-v2a` #27, `chutoro`).

### P6. Configuration, tiering, and determinism

- `ProptestConfig { cases: 1, .. }` "reduces property-based testing to a
  parameterised test with a single random parameter" and signals
  unresettable process-global state; add a test-only reset hook instead
  (`tei-rapporteur` #86).
- Documented budgets not enforced: docs promised 100,000 cases while the
  block used the default; the reviewer then added the counter-pressure
  that hardcoding 100,000 slows CI, so read it from an environment
  variable (`wireframe` #356).
- `fork` and case count are independent knobs that multiply: forking
  derived from one variable while cases were capped separately blew a
  600 s CI timeout (`chutoro` #130). A cap only works if the runner
  consumes the capped value; a downstream profile loader re-reading
  `PROPTEST_CASES` silently overrode it (`chutoro`).
- Wall-clock limits as pass/fail assertions inside a property are
  rejected; use a deterministic fuel budget and a separate watchdog
  (`netsuke`).
- "Seeded" is not deterministic if `HashMap` is involved: "`RandomState` is
  outside Proptest's seed, so shrinking silently discards valid candidates
  and committed regression seeds are decorative" (`netsuke` #700).
- Do not describe `ProptestConfig::default()` as deterministic (`dbar`);
  when standardizing a fixed seed, keep `PROPTEST_RNG_SEED` overridable
  (`chutoro`).
- Properties that mutate the process environment must acquire the
  environment lock inside the strategy helper, never across a `proptest!`
  iteration boundary (`netsuke`).
- Properties that depend on the runner giving each test its own process
  are not portable between `cargo test` and `cargo nextest`
  (`tei-rapporteur`).
- Unnecessary platform gating means CI on other platforms never exercises
  a portable invariant (`pg-embed-setup-unpriv` #153).

### P7. Regression files

- Proptest keys persistence files to the declaring source file. Renaming
  or extracting a property file without renaming its
  `.proptest-regressions` leaves saved seeds unreplayed (`netsuke`).
- A proptest source both `#[path]`-included by another integration test
  and discoverable as its own target runs twice in different binaries
  with two regression paths, orphaning seeds (`netsuke` #497).
- Mutation testing generates seeds from deliberately injected defects; do
  not commit those, and do not blanket-ignore the directory either.
  Disable persistence during mutation runs (`cuprum`).

### P8. Layout, lint, and packaging

- The estate-wide 400-line file cap is the most common reason a proptest
  addition triggers a refactor mid-review. Put `proptest!` blocks and
  strategies in a sibling module from the start (`tests_proptest.rs` plus
  `tests_proptest_strategies.rs` in `repovec-appliance` #23;
  `prop_tests.rs` per module in `rstest-bdd`). The counter-finding:
  `spycatcher-harness` noted that a sibling file can make automated
  coverage checks believe the module is untested, so follow the
  repository's convention rather than a universal rule.
- Every module, including proptest and strategy modules, needs a `//!`
  doc comment.
- Large deterministic fixture data goes in an external file loaded with
  `include_str!` (`chutoro`).
- A `proptest!` block whose inner functions lack `#[test]` compiles, runs
  nothing, and passes: "The `proptest!` macro tests may not be generating
  test cases as expected... but the code compiles and all 3494 tests
  pass" (`axinite` #107).
- `Box::leak` to coerce `String` to `&'static str` leaks once per
  generated case (`rstest-bdd` #492).
- An unused `proptest` dev-dependency is itself treated as evidence of a
  gap (`femtologging`).
- Dependency pins: `mdtablefix` and `netsuke` require explicit versions
  rather than `proptest = "1"`; `frankie` and `tei-rapporteur` asked for a
  current release; `tei-rapporteur` uses `proptest = { workspace = true }`
  and objected to calling it a "workspace dev-dependency".
- Strategy-builder method chains (`.prop_filter`, `.prop_map`) interact
  with `rustfmt` and Clippy thresholds like any other code; reviewers
  apply cognitive complexity ≤ 9, max args ≤ 4, and max nesting ≤ 4 inside
  `#[cfg(test)]` code.

## Failure modes: Kani

Frequency across the three sets (159 findings):

| Category                              | Count |
| ------------------------------------- | ----- |
| vacuous-or-reimplemented-harness      | 24    |
| makefile-or-ci-shape                  | 20    |
| docs-or-overclaiming                  | 20    |
| version-pin-or-install-route          | 15    |
| lint-interaction                      | 14    |
| missing-harness                       | 13    |
| model-mirror-drift                    | 10    |
| cfg-kani-gating                       | 10    |
| solver-timeout-or-cliff               | 5     |
| mutation-evidence                     | 4     |
| assert-macro-choice                   | 4     |
| unwind-bound                          | 3     |
| stub-or-unsupported-feature           | 3     |
| not-run-in-ci                         | 3     |
| over-constrained-assume               | 2     |

Plumbing (Makefile and CI shape, pins and install route, lint
interaction, cfg gating, not-run-in-ci) totals 62 of 159, more than the
harness-quality categories combined. Getting Kani to run and stay run is
a bigger review cost than writing the harness.

### K1. Vacuous or reimplemented harnesses

- A placeholder left behind: "`scaffold_smoke` is a placeholder
  `kani::assert(true)` proof, not a substantive invariant proof"
  (`netsuke` #336). Sibling harnesses "build errors directly (no
  `from_manifest`/`resolve_rule`/`find_duplicates`), so tests don't
  exercise changed logic".
- A harness calling a hand-written mirror of the production function
  proves the mirror (`whitaker` #187 and others): "a Kani harness that
  only asserts against a hand-rolled model helper ... proves the model is
  self-consistent, not that production code preserves the invariant".
  `chutoro` ADR-002 retired a 3-node bidirectionality harness for
  exactly this reason: it inserted the reverse edges itself and "cannot
  detect missing reciprocity in production code".
- Pointer-identity selection: comparing `&'static str` addresses to choose
  which assertion fires, with `kani::assume(false)` on the fallback,
  "becomes vacuous instead of checking the distance result" (`chutoro`
  #129, flagged by three reviewers).
- `kani::assume(false)` inside production code "prunes every overflow path
  globally in Kani builds, so any current or future harness that forgets
  to bound `payload_len` will still appear to verify" (`mxd` #283). State
  preconditions at each harness's call site through typed symbolic
  inputs.
- `if let Ok(forest) = parallel_kruskal(...) { ... }` skips verification
  entirely on the error path; `Option::unwrap_or(false)` ahead of a
  negative assertion passes vacuously on `None`. Assert `Some`/`Ok` first
  and fail loudly with `kani::assert(false, msg)` on unexpected arms
  (`chutoro`).
- Missing `kani::cover!`: "every Kani harness with branching logic needs
  `kani::cover!` on each branch" (`cuprum`), and `theoremc` enforces it at
  schema level (a non-empty witness list unless `allow_vacuous` with a
  written `vacuity_because`).
- An assertion that structurally cannot fail (bounds-checking a type that
  cannot violate the bound) gives false assurance (`whitaker`).
- Inclusion without exclusion: "None of the harnesses assert that
  `build_adjacency` *only* emits edges that were present in the input"
  (`whitaker` #186). Prove both directions.
- Coverage claims wider than the symbolic inputs: a harness claiming
  multi-level coverage with the level hardcoded to `0` (`chutoro`).
- Runtime early returns narrow the harness silently; prefer `const`
  assertions or `kani::assume` (`mxd`).
- A proof that misuse is "currently harmless" is the wrong artefact;
  narrow the production API instead (`cuprum` #242).

### K2. Model-mirror drift

- Kani-only parallel structs (`KaniCommitUpdate`, `KaniCommitContext`)
  were deleted in favour of production types (`chutoro` #73). Wire
  harnesses to production types wherever possible.
- A shared driver: "`drive` is identical in both files. Move it into
  `pump_machine.rs` behind `#[cfg(any(test, kani))]` and make it
  `pub(crate)`" (`cuprum` #242). Convention: proptest under
  `#[cfg(test)]`, harnesses under `#[cfg(kani)]`, shared helpers under
  `#[cfg(any(test, kani))]`.
- A compressed proof-seam view must preserve exact production equality
  semantics, or "the harness proves invariants over states production
  cannot reach" (`whitaker` #232). A single-slot dedup check silently
  weakened a proof that still passed.
- Harness assertions must route through the production invariant helper
  (`is_bidirectional`), not a re-derivation (`chutoro`).
- Kani-only helpers must assume the same preconditions production
  enforces, so a missing node cannot become an empty state (`chutoro`).
- Refactors change traversal shape: "explicitly check whether the refactor
  changes loop/traversal shape in a way that could blow the harness's
  `#[kani::unwind(...)]` bound" (`netsuke`); `StringOrList::map_each`
  must use indexed traversal to stay tractable.
- Kani-only twin constructors should share one validation helper with the
  production constructor (`chutoro`).
- When a full parallel Kani-only reimplementation is the right call (to
  avoid `BTreeMap`/`Vec` drop-path unwinding), record the state-explosion
  evidence in the ExecPlan so "reduce duplication" can be declined with
  numbers (`whitaker`).

### K3. Solver cliffs and bounds

- Collections are the enemy: "the verifier lowers the real `HashMap` and
  hashing implementation. The proof budget is spent in collection, serde,
  and hashing internals before the IR invariant is reached" (`netsuke`
  ADR-004). The accepted fix was a private `cfg(kani)`-only `IrHashMap`
  behind a `not(kani)` type alias, not a public verification port.
- The kernel extraction pattern: "the direct end-to-end
  `canonicalize_cycle` proof verifies N=2 in 177 seconds but N=3 exhausts
  the 8 GiB memory cap"; after extracting `canonicalize_cycle_by<T>`
  proved over `u8`, "Kani now verifies N=2 in 4.6 s, N=3 in 7.6 s, and
  N=4 in 11.8 s" (`netsuke` #392). Recompute unwind bounds after such a
  refactor; nested loops need N², not N.
- "For bounded model checking, `HashSet` introduces additional symbolic
  state"; an O(n²) nested scan was accepted instead (`chutoro` #75).
- Code-health refactors can inflate the CBMC formula past the solver:
  "kissat: error: parse error: maximum variable index exceeded"; validate
  any such refactor against `make kani-full` in isolation (`chutoro`
  #227).
- A directly requested harness measured intractable ("timed out after
  twenty minutes... 2,590 aborted paths") was deferred with the
  measurement recorded and an equivalence-test proxy substituted, and the
  reviewer accepted it (`chutoro` #227). Measure; do not assert
  difficulty.
- Production scanners exceed the "five-minute, 8 GiB" cap at six to eight
  symbolic characters, so proofs target 8- and 32-character windows and
  proptest fills the gap to 256 characters (`netsuke`).
- Bounded inputs (`<= 128`) can exclude the branches that only trigger
  outside the bound, such as overflow handling; add an unbounded smoke
  harness or document the gap (`whitaker`).
- Bind unwind literals, fixed-array capacities, and production constants
  together with `const` assertions; where `#[kani::unwind]`'s literal-only
  argument prevents it, document the coupling (`whitaker`).
- `wireframe` prefers `#[kani::unwind(N)]` on the harness over
  `--default-unwind` because "it reduces accidental overconfidence".
- Document the concrete numeric bounds a harness proves next to the
  harness, not "bounded payloads" (`mxd`).

### K4. `cfg(kani)` gating and lint interaction

- `#[cfg(kani)]` code is invisible to the normal lint gate: a stale unused
  import under `cfg(kani)` survived `-D warnings` (`cuprum` #242). Only a
  Kani build surfaces drift there.
- `#[cfg(kani)]` is not `#[cfg(test)]`: Clippy's allow-expect-in-tests
  exemption does not apply, so `.expect()` in a harness helper is a lint
  failure in repositories that deny it (`chutoro`).
- A new call into a `cfg(test)`-only helper from code that also compiles
  under `cfg(kani)` breaks every harness in the crate (`chutoro`).
- `#[allow(dead_code)]` as a gating workaround is rejected: "Those
  attributes hide a real mismatch between the selected configuration and
  the compiled code" (`chutoro`). Use narrowly scoped
  `#[expect(lint, reason = "...")]`; `whitaker` forbids `#[allow]`
  outright, in sidecars too. Do not gate genuinely dead code behind
  `#[expect(dead_code)]` claiming it is a Kani seam unless a harness calls
  it.
- Complexity gates apply inside harnesses: cognitive complexity ≤ 9, max
  lines per function ≤ 70, max args ≤ 4, plus CodeScene method-size gates.
  Group parameters into a struct early; factor shared symbolic-input setup
  into one helper; near-identical per-metric proofs trip duplication gates.
- `trybuild` UI fixtures that include `cfg(kani)` modules scope the
  suppression to the `mod` declaration:
  `#[expect(unexpected_cfgs, reason = "trybuild's crate inherits no
  check-cfg")]`, never a crate-level `#![allow]` (`cuprum`).
- Adding `cfg(kani)` gating should ship `trybuild` compile-pass tests for
  the gating (`netsuke` has `tests/kani_cfg_ui_tests.rs`).
- Centralize the `cfg(kani)` versus `cfg(not(kani))` divergence into one
  small helper rather than duplicating whole functions (`netsuke`).
- `cargo-mutants` does not evaluate `cfg(kani)`, so harness modules must
  be in the mutants exclude globs or their survivors are noise
  (`netsuke`, `wireframe` workflow-contract tests).
- A `const fn` that compiles on the workspace toolchain can fail under
  Kani's bundled, older nightly (`netsuke` #577); PyO3 entry points cannot
  be `const` (`cuprum`).
- Kani does not use the repository toolchain: "Selecting
  `+nightly-2026-08-23` or setting `RUSTUP_TOOLCHAIN=...` does not safely
  upgrade the installed Kani compiler. It can create a mismatched driver,
  sysroot, and compiler-library set" (`netsuke` #577). Kani 0.67.0 bundles
  a nightly that predates Polonius by default, which matters for any
  repository mid-migration.
- Kani cannot model FFI into an embedded interpreter (PyO3), default
  `HashSet` `RandomState` entropy syscalls on some versions, or async I/O
  boundaries (`tei-rapporteur`, `axinite`, `vk`). Make the gate fail
  closed and track the blocker, or use proptest instead.

### K5. Makefile, CI, pins, and install route

- `--locked` does not pin the verifier: "Install an approved exact version
  with `cargo install --locked kani-verifier --version
  <approved-version>`" (`chutoro` #227). The fix derived `KANI_VERSION`
  from `tools/kani/VERSION`; `netsuke` goes further and requires pinned,
  checksum-verified prebuilt bundles.
- A pin file is only an enforced pin if something checks it
  (`prover-tools kani check-version`); a checksum-presence assertion is
  not a checksum-binding assertion (`netsuke` #664).
- Targets must delegate: `wireframe` tests forbid bespoke `cargo
  install`, `curl`, `unzip`, `sha256sum`, and `rustup toolchain install`
  in verification recipes. Do not invent `prover-tools kani run`; the
  pinned CLI has no Kani execution subcommand, and documentation must say
  the target is a placeholder until it does (`wireframe` #541).
- Makefile hygiene: use `$(CARGO)` and `$(PROVER_TOOLS)` variables, `override
  :=` for values sourced from a pin file so an inherited environment
  variable cannot repoint the toolchain, real tabs in recipes (a
  `missing separator` regression recurred verbatim in `weaver` #106 and
  #128), and redaction of `KANI_*_FLAGS`/`VERUS_*_FLAGS` before logging.
- Kani must not enter `make test`, `make lint`, `make check-fmt`, or
  `make all` (`netsuke`); `axinite` chose the opposite, a fail-closed
  formal gate inside `make all`. Either is acceptable if documented.
- CI: nightly jobs need a `concurrency` group; date gating should use a
  rolling window, not calendar-day equality, or fresh commits are skipped;
  clock skew should be a soft skip; path filters must include every
  package manifest the gated command compiles; cache keys must hash every
  input and be version-qualified; composite actions must declare the
  environment they render keys from; contract tests must glob `*.yml` and
  `*.yaml`.
- Contract tests assert step order by position (restore, install,
  version-check, run), not presence; key cache assertions by tool identity;
  implement `actions/cache` glob semantics rather than substring checks;
  assert the installer's executable bit in the Git index.
- Kani-conditional steps on heterogeneous runners must probe for
  `cargo-kani` and emit a visible skip diagnostic with infallible
  `eprintln!`, not `writeln!(stderr)?` (`theoremc` #42).
- `LD_LIBRARY_PATH` for Kani's toolchain must be derived from `cargo kani
  --version`, never a contributor's home directory (`cuprum`); sidecar
  scripts must branch on `uname -s` for `DYLD_LIBRARY_PATH`, export
  `RUSTUP_TOOLCHAIN` explicitly, keep harness names in step with
  `#[kani::proof]` names, and check whether `--harness` is repeatable
  before relying on it (`whitaker`).
- The `prover-tools` CLI itself: every `--repo-root`-relative override
  must resolve as `repo_root / path`; option constructors must forward
  every caller-supplied option on the fallback branch too; tests must
  sanitize `INPUT_*` from the environment (`rust-prover-tools` #6 and
  follow-ups).
- Mutation evidence for the evidence: a contract test running `git apply
  --check` inside cargo-mutants' non-git copies reported every mutant as
  killed (`netsuke` #608). Detect non-git trees and skip.

### K6. Documentation and overclaiming

Twenty findings are about the prose around a harness rather than the
harness. Reviewers cross-check ExecPlans, ADRs, design docs, and the
developers' guide against the code and against each other:

- Every harness must be in the developers' guide inventory table before
  merge; partial documentation fails the check (`netsuke`).
- A retrospective must not claim a gate succeeded where the same document
  records it failing (`chutoro`).
- Retired harnesses need the design narrative updated in the same change.
- Unwind bounds tuned during review must be updated in every place they
  are stated (prose, script default, artefacts) in the same commit, or
  the bot re-flags each stale value for several revisions (`whitaker`).
- Every `#[cfg(kani)]`-only `pub(super)` helper needs rustdoc covering
  the why (proof tractability) as well as the what; CodeRabbit repeats
  the request until both are present.
- Deliberate simplifications (omitting path compression) must be
  documented so nobody "fixes" them into a state-space explosion.
- Behaviour that differs under `cfg(kani)` (panic versus abort) belongs in
  the public doc comment.
- Docs must not invent CLI surface, must use real tabs in Makefile
  snippets, and follow en-GB-oxendict spelling even in
  `tools/verus/README.md`.
- ExecPlan `Status:` fields and checkbox lists must agree with the
  narrative.

### K7. Missing harness, and when not to add one

Thirteen findings requested a harness. The requests cluster on
`unsafe` (`from_utf8_unchecked`, a lifetime-extending `transmute`,
`Send + Sync` claims), index and drain arithmetic whose safety rests on
an external invariant, dispatch selectors, and small pure validators.
Reviewers explicitly reject Kani for invariants the type system already
enforces, for async Hyper I/O boundaries, for PyO3/GIL interactions, and
for anything reachable only through real syscalls (refactor to a pure
state machine over an event enum first, `cuprum`). A bundled request
("proptest and Kani") must be tracked as two follow-up items, or the
Kani half falls through (`podbot`, `weaver`). Omitting a harness in favour
of proptest needs a written justification in the developers' guide
(`rstest-bdd` #528).

## Failure modes: Verus

Verus is thinly represented (28 findings from four repositories) because
only `chutoro` and `whitaker` have shipped proofs. Almost half the
findings concern install scripts that `prover-tools` has since replaced.

| Category                         | Count |
| -------------------------------- | ----- |
| toolchain-or-install             | 13    |
| docs-or-overclaiming             | 4     |
| proof-structure                  | 3     |
| spec-mirror-drift                | 2     |
| lint-suppression                 | 2     |
| assume-or-admit-left             | 1     |
| tautological-lemma               | 1     |
| verification-result-masking      | 1     |

### V1. Proof structure

- A lemma that `ensures` a compound property (`total_ordering`) via a
  single bare `assert` "appears to rely on an unproved `assert`, so the
  Verus proof likely won't verify" (`chutoro` #82). Split into one helper
  lemma per property (`lemma_edge_ord_reflexive`,
  `lemma_edge_ord_antisymmetric`, ...) and compose.
- A lemma of the form `spec_predicate(x) <==> definition_of(spec_predicate)`
  proves nothing (`whitaker` #170).
- Axioms at a trust boundary must be propagated into the `requires`
  clause of every wrapper lemma, not only the leaf (`whitaker`).
- Specialize scaffolding to the concrete type verified rather than keeping
  speculative generics.

### V2. Spec-mirror drift and refinement

- "A Verus proof over an idealised data structure (e.g. `Seq<nat>`) does
  not, by itself, prove anything about a differently-shaped runtime
  structure (e.g. a sparse `BTreeMap`) unless an explicit
  abstraction/refinement lemma bridges the two" (`whitaker` #170): "the
  lemmas here do not justify the shipped implementation". Deferred to an
  issue.
- A Verus sidecar importing a production type via `#[path]` needs a CI
  script asserting the path and type still exist, because Verus does not
  link against production code (`whitaker` #218).
- Spec items are public API; document each spec function's relationship
  to the runtime model (`whitaker`).
- `wireframe`: "Do not ignore Verus trigger warnings... Chutoro is right
  about this."

### V3. Toolchain, install, and gating

All of these are now the job of `prover-tools verus install|run`, and
are recorded here as the reasons the route is mandatory:

- Downloading a release without checksum verification (`chutoro` #82).
- A runner capturing `$?` from a negated `!` compound, always 0, which
  "defeated the new gate" (`chutoro` #82); a runner iterating several
  proof files but propagating only the last exit status (`whitaker`).
- Multiple `trap` calls on the same signal overwriting each other; flag
  versus positional confusion breaking `--version` passthrough; sibling
  script paths resolved from the caller's cwd; `rustup install` versus
  `rustup toolchain install`; toolchain identifiers with channel and date
  suffixes; Bash 3.2 portability (`whitaker`).
- In `prover-tools` itself: the install-fallback branch dropped the
  caller's target (`rust-prover-tools` #6); `rustup` must be required only
  when the version probe fails.
- Keep Verus out of pull-request gates and `make all` until proofs are
  stable (`netsuke`), and do not add it "until there is something small
  and stable enough to prove" (`axinite`).
- `#[allow]` is forbidden in `verus/` files exactly as in production;
  use `#[expect(dead_code, reason = "...")]` on specific spec-only items,
  never a blanket module attribute. Rustdoc `///` is required even on
  `pub(super) proof fn`.

## Verification omitted, then requested, then landed

Across the three triage sets, 109 findings on roughly 100 distinct pull
requests were tagged as a reviewer asking for a property test, harness,
or proof the change lacked, with evidence it landed before merge. The
breakdown by tool is proptest 62, cross-cutting 17 (multi-tool
requests), Kani 3, Verus 0, prover-tools 1 (a contract-test request), and
about 25 more filed under the tool-specific `missing-*` categories with
resolution `fixed`. The per-repository picture:

| Repository            | Same-PR landings noted |
| --------------------- | ---------------------- |
| netsuke               | 25                     |
| mdtablefix            | 15                     |
| rstest-bdd            | 11                     |
| weaver                | 8                      |
| axinite               | 5                      |
| spycatcher-harness    | 3                      |
| stilyagi              | 3                      |
| theoremc              | 3                      |
| wildside              | 3                      |
| chutoro               | 3                      |
| whitaker              | 4                      |
| others (≤2 each)      | 16                     |

What the pattern looks like:

- The request almost always arrives as the CodeRabbit pre-merge row
  "Testing (Property / Proof)", a warning rather than an error, not as a
  line comment. It recurs verbatim across review rounds until satisfied,
  and it can regress from Passed to Warning inside one PR as the invariant
  surface grows (`mapsplice` #76, `spycatcher-harness` #43).
- The triggering code is usually a parser, canonicalizer, path or
  identifier normalizer, merge or precedence rule, bounded queue, or a
  small validator: an invariant "over a range of inputs, states,
  orderings, or transitions" where the PR shipped two to four `rstest`
  cases.
- What lands is typically one sibling `*_proptests.rs` or `prop_tests.rs`
  file with two to six properties (round-trip, idempotence, determinism
  across orderings, rejection of out-of-range input), sometimes an
  extended strategy on a second round. Kani landings are rarer and follow
  a request on `unsafe` or ownership code (`cuprum` #160, #232;
  `whitaker` #186).
- Authors who push back on enumerability lose unless the space is small
  and exhaustively run every time (`rstest-bdd` #532 versus #686). The
  human reviewer's standing instruction, quoted in at least four
  repositories, settles it: "Do not treat warnings as optional or
  aspirational. Where a change is out of scope for this PR, propose a
  GitHub issue unless one exists already."
- Deferral is accepted when tracked: `netsuke` answered a run of warnings
  with dedicated follow-up PRs (#305 Kani tooling, #308 Kani smoke CI,
  #325 IR property tests, #336 manifest-to-IR harnesses, #359 property
  tests for `expand_foreach`), and `cuprum` #62 deferred to issues paid in
  #93.
- The bot's "✅ Addressed" marker was wrong three times, always on
  proptest requests; the real evidence trail is the follow-up prompt
  "@leynos Has this now been resolved in the latest commit? Use codegraph
  analysis to determine your answer" and the check flipping to Passed with
  a citation such as "Use the added proptest over `any::<u8>()`"
  (`stilyagi`).

A confirmation pass then checked every candidate against GitHub with a
strict definition: a reviewer asked for a proptest property test, a Kani
harness, or a Verus proof the PR lacked, **and** the PR merged with that
artefact literally present in its diff (`proptest!` or `prop_assert*`,
`#[kani::proof]`, `verus!` or `proof fn`). Conventional `rstest`, unit,
snapshot, or `trybuild` tests, Python Hypothesis, JavaScript fast-check,
and prose recommendations do not count.

| Confirmation outcome                         | PRs |
| -------------------------------------------- | --- |
| Candidates checked                           | 228 |
| Confirmed (artefact in the merged diff)      | 124 |
| Refuted                                      | 103 |
| Inconclusive                                 | 1   |

Refutation reasons: never merged at the time of the check (37),
conventional test added instead (27), a non-Rust substitute such as
Hypothesis (10), the artefact never added before merge (9), deferred to
a tracked issue (9), docs-only PR (6), declined with a recorded reason
(1), and a handful of misclassifications. Confirmed cases by tool:
proptest 118, Kani 3, both 2, Verus 0. By requesting reviewer, counting a
PR once per reviewer that raised it: the pre-merge "Testing (Property /
Proof)" row 96, CodeRabbit line comments 60, the human maintainer 18,
Sourcery 3, `chatgpt-codex-connector` 1. The per-repository table is in
[Appendix B](#appendix-b-confirmed-omission-cases).

## Barriers to entry

Reading the findings as a first-time adopter would, the on-ramp problems
are:

1. **Not knowing whether the change needs a property test at all.** The
   trigger rule is written down in repository guidelines but not in the
   skills, so implementers either skip it (197 `missing-property`
   findings) or add it where it is unwanted (`podbot` #99, `netsuke`
   #540).
2. **No template for the first property file.** Reviewers want a sibling
   file with a `//!` comment, strategies separate from properties, the
   repository's `.expect`/`prop_assert` policy respected, no branching in
   the body, and an explicit `ProptestConfig` only when justified. None of
   that is discoverable without reading a prior PR.
3. **The strategy is the test.** The most frequent quality finding is a
   generator that cannot reach the claimed shape. There is no habit of
   auditing what the strategy covers against the documented input
   grammar before writing assertions.
4. **`cfg(kani)` is a different build.** Harness authors are repeatedly
   surprised that Clippy, `cargo-mutants`, the normal `-D warnings` gate,
   and even the Rust toolchain differ under `cfg(kani)`. The costs
   (invisible unused imports, `.expect` lint failures, `const fn`
   breakage, mutants noise) all land at review time.
5. **The install route is still contested.** Half the mature adopters
   vendor scripts that `prover-tools` replaced, and the review history of
   those scripts is long. New repositories copy whichever neighbour they
   look at.
6. **No vocabulary for "measured intractable".** Authors either
   over-promise coverage (docs-or-overclaiming, 20 findings) or drop a
   request silently. The accepted move (record the timing, substitute an
   equivalence test, open an issue) is not written anywhere reusable.
7. **Prose is part of the proof.** A large share of Kani and Verus review
   churn is the developers' guide inventory, ExecPlan status fields,
   unwind values stated in three places, and captions overstating
   coverage.
8. **Verus has no compiled link to production.** Spec mirrors, `#[path]`
   imports, and idealized sequences all drift unless a refinement lemma or
   a CI existence check binds them, and the skill did not say so.
9. **Contract tests are expected, not optional.** `wireframe`, `netsuke`,
   and `chutoro` all gate the Makefile and CI shape with tests; a PR that
   adds a target without a contract test draws a "Testing (Overall)"
   error.

## Conventions reviewers enforce

Estate-wide, in addition to the trigger rule and the "warnings are not
optional" instruction quoted above:

- 400-line file cap, applied to tests, harnesses, and proof files.
- A `//!` module comment on every module, including sidecars.
- en-GB-oxendict spelling (`-ize`, `-yse`, `-our`) everywhere, including
  `prop_assert!` messages and tool READMEs; uncommon acronyms (CBMC, ADR,
  HNSW, MST) expanded on first use in design docs.
- Non-vacuous tests "that would fail for plausible incorrect
  implementations"; a mutation must be caught.
- Conditionals with more than two branches extracted into a predicate.
- Clippy thresholds (cognitive complexity ≤ 9, max args ≤ 4, max nesting
  ≤ 4, lines per function ≤ 70) applied to `#[cfg(test)]` and
  `#[cfg(kani)]` code; `#[expect(lint, reason = "...")]` over `#[allow]`.
- Roadmap and issue linkage: a landed property test closes its issue with
  evidence.

Per-repository variations that a skill can only flag, not resolve:
`.expect` preferred (`axinite`, `mxd`, `wireframe`) versus denied
(`netsuke`, `tei-rapporteur`); Kani inside `make all` (`axinite`) versus
excluded (`netsuke`); proptest inline (`chutoro`, `mdtablefix`) versus
sibling files (`netsuke`, `rstest-bdd`, `zamburak`); `chutoro`'s shared
`ProptestRunProfile` for environment-driven tiering.

## Implications for the skills

- **P1 missing-property and omitted-then-requested.** `proptest` gains an
  "Is a property test expected?" decision rule with the three accepted
  answers, and a scope-statement template in
  `references/sibling-module-template.md`. `rust-verification` gains the
  trigger rule and the pre-merge check behaviour.
- **P2 and P3 strategy and oracle weaknesses.** `proptest` gains a
  strategy audit step before assertions, tautology and disjunction
  anti-patterns, the oracle-construction rule, and
  `references/review-failure-modes.md`.
- **P4 assume and filter misuse.** `proptest` states precondition
  ordering, environment guards outside the block, and the early-return
  rule.
- **P5 assertion policy.** `proptest` tells the reader to read the
  workspace lint table first and to route helpers through
  `TestCaseError`; the reference lists the per-repository policies.
- **P6 and P7 configuration, determinism, regressions.** `proptest`
  gains the `RandomState` warning, the fork-times-cases cost, the
  `PROPTEST_CASES` override trap, persistence keyed by source file, and
  the mutation-run persistence rule.
- **P8 layout and lint.** `proptest` gains the sibling-module template
  with `//!` docs, the 400-line cap, and `#[test]` inside `proptest!`.
- **K1 and K2 vacuous harness and drift.** `kani` gains a review-bar
  section, `kani::cover!` in the core concepts and worked harness, the
  shared-driver pattern under `#[cfg(any(test, kani))]`, and the
  both-directions rule.
- **K3 cliffs.** `kani` gains the kernel-extraction pattern, the
  "measured intractable" protocol, and N² unwind for nested loops.
- **K4 cfg and lint.** `kani` gains "`cfg(kani)` is a different build"
  with the checklist of what does not see harness code.
- **K5 and prover-tools.** `kani` and `verus` gain
  `references/project-on-ramp.md`: pin files, Makefile targets that
  delegate to `prover-tools`, smoke and nightly CI, contract tests, and
  mutation evidence.
- **K6 documentation.** `kani` gains the harness inventory duty and the
  doc-sync checklist in its review reference.
- **V1 to V3.** `verus` gains lemma decomposition as a review
  expectation, the restated-definition and unpropagated-axiom
  anti-patterns, the two production bridges with the refinement-lemma
  requirement, the `#[path]` existence check, gating advice, and the
  lint policy for `verus/`.

## Uncertainties

- Keyword digests truncate long threads; 30% of findings have unknown
  resolution, so the omission counts are lower bounds.
- Frequency comparisons across repositories reflect reviewer verbosity
  and review-round count as much as defect rate.
- The pre-merge check taxonomy is inferred from the estate's shared
  CodeRabbit configuration as observed; the configuration itself was not
  read.
- Verus conclusions rest on two repositories and one tool repository.
- Python Hypothesis, Loom, TLA+, and Stateright findings were excluded
  and may hold transferable lessons.

## Appendix A: repository coverage

Repositories with findings, and the count of findings each contributed:
see the per-repository digest statistics retained with the survey
artefacts. Repositories in scope with no relevant findings were
`fingermouse`, `jmap-wasm`, `mdast-check`, `msgspec-crockford`, `rustxt`,
and `ytmusic-wasm` (no hits), plus `agentland`, `dear-diary`, `memoryd`,
`monotony`, `skyjoust`, `comenq`, `rentaneko`, `evert`, `limela`, and
`mpsc-log` (hits were Python Hypothesis recommendations or passing check
rows).

## Appendix B: confirmed omission cases

Confirmed cases by repository, with the number of candidates the
confirmation pass checked for that repository:

| Repository            | Confirmed | Checked |
| --------------------- | --------- | ------- |
| netsuke               | 35        | 42      |
| mdtablefix            | 20        | 29      |
| axinite               | 10        | 13      |
| rstest-bdd            | 10        | 16      |
| chutoro               | 6         | 12      |
| weaver                | 6         | 11      |
| wireframe             | 5         | 8       |
| whitaker              | 4         | 14      |
| cuprum                | 3         | 6       |
| podbot                | 3         | 4       |
| repovec-appliance     | 3         | 8       |
| spycatcher-harness    | 3         | 6       |
| stilyagi              | 3         | 3       |
| theoremc              | 3         | 3       |
| ortho-config          | 2         | 4       |
| wildside              | 2         | 12      |
| catnap                | 1         | 2       |
| lag-complexity        | 1         | 1       |
| lille                 | 1         | 5       |
| tei-rapporteur        | 1         | 3       |
| wildside-engine       | 1         | 2       |

Representative confirmed cases, with what the reviewer asked for and
what landed:

- `axinite` #74: "Exercise `char_boundary_truncation()` over generated
  UTF-8 strings and bounds, not just the two hand-picked examples."
  A `proptest!` block over generated strings and bounds landed.
- `axinite` #154: "Add `proptest` coverage that asserts sensitive query
  values never survive sanitization across arbitrary key casing,
  encoding, absolute URLs, and relative URLs." A block in the sanitizer
  module landed after the bot's first "addressed" marker was challenged.
- `axinite` #176: the pre-merge row noted that `proptest = "1.6.0"` was
  in `Cargo.toml` but the referenced `prop_tests.rs` did not exist; the
  file landed.
- `chutoro` #125 (`chatgpt-codex-connector`): "this suite still passes
  because `query_points_fixture()` only chooses finite rows"; a
  non-finite fixture strategy and a canonicalization property landed.
- `chutoro` #227: a direct Kani harness on base-layer healing was
  requested; it was measured intractable, an equivalence test was
  substituted, and a workflow-contract test landed. Counted as confirmed
  for the contract test, not the harness.
- `cuprum` #93 and #160: a human audit found "no Rust-level `#[test]`,
  `proptest`, `kani`, or `verus` coverage" in the native extension; a
  UTF-8 decoder property against `String::from_utf8_lossy` and two
  splice-loop properties landed, followed by Kani harnesses for the
  borrowed-descriptor invariant in #232.
- `lille` #285: an ADR rejecting proptest, Kani, and Verus was overruled
  because `i64` weights and path strings are not finite domains; a
  workspace `proptest` dependency and a `properties.rs` module landed.
- `mdtablefix` #303: "unsafe UTF-8 truncation with unchecked byte
  indexing; proptest property tests are needed to verify invariant that
  panics never occur on arbitrary input." A `\PC*` strategy asserting
  char-boundary safety landed.
- `mdtablefix` #308: the first property covered only the positive case;
  the landed test carries both branches of the width condition.
- `mdtablefix` #350: the maintainer asked the bot to "propose a property
  test design for this functionality and provide an AI coding agent
  prompt", and the resulting date-predicate properties landed.
- `mdtablefix` #368: the reviewer noted the property asserted only sort
  order; a line-count preservation assertion was added.
- `spycatcher-harness` #43: locale parsing with three or four fixed
  locales; a property landed, then the strategy was widened to full
  BCP 47 syntax on the next round.

The shape of what lands is consistent: one new sibling module or one
`proptest!` block inside the existing test module, two to six
properties named for the invariant, a generator per input class, and in
the stronger cases an oracle drawn from a standard-library or reference
implementation. Kani landings are rare and follow requests on
ownership or `unsafe` code. No Verus proof landed in response to a
review request during the survey window.
