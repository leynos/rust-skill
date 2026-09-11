# Changelog

All notable changes to this project are recorded in this file.

The format is based on [Common Changelog](https://common-changelog.org).

## [Unreleased]

### Added

- `docs/verification-review-failure-modes.md`: a compendium of recurring
  review findings on `proptest`, Kani, and Verus work across the
  `leynos` estate (57 repositories, 9,171 pull requests, 851 triaged
  findings), the standard `rust-prover-tools` integration shape, the
  123 confirmed cases where verification was omitted, requested by a
  reviewer, and landed before merge, and the barriers to entry each
  skill now addresses.
- `proptest/references/review-failure-modes.md` and
  `proptest/references/sibling-module-template.md`: the pre-submission
  checklist drawn from estate review history, and the sibling
  `prop_tests.rs` plus `prop_strategies.rs` layout with a scope-statement
  template for changes that need no property test.
- `kani/references/project-on-ramp.md` and
  `kani/references/review-failure-modes.md`: pin files, `check-cfg`,
  Makefile targets that delegate to `prover-tools`, smoke and nightly CI
  jobs, contract tests, mutation evidence, and the harness inventory; plus
  the vacuous-harness, model-drift, solver-cliff, and `cfg(kani)`
  checklist.
- `verus/references/project-on-ramp.md` and
  `verus/references/review-failure-modes.md`: when Verus is due, pins and
  `prover-tools` targets, layout, the two production bridges (spec mirror
  and `#[path]` import) with their maintenance duties, lint policy, and
  the lemma-structure and refinement findings.
- `rust-unit-testing` skill: covers Rust unit-test helper shape with
  `rstest` fixtures and parameterized cases, `serial_test` isolation,
  fallible setup, rich assertions through `googletest` and
  `pretty_assertions`, and `insta` snapshots. Ships a worked helper-refactor
  reference that separates dynamic error-source extraction, pure comparison,
  and assertion formatting.
- `rust-verification` skill: routes Rust verification work to the
  smallest adversary that matches the failure mode (Miri, sanitizers,
  proptest, cargo-mutants, turmoil, loom, shuttle, Kani, Verus). Ships
  with two references: per-tool rationale and the determinism fences
  that chaos tools require.
- `arch-supply-chain` skill: frames the dependency graph as a
  deliberately shaped trust surface. Covers cargo-audit, cargo-deny,
  cargo-vet, cargo-semver-checks, cargo-public-api, lockfile policy,
  and MSRV pinning. References cover the cargo-vet trust model and
  day-to-day dependency hygiene patterns.
- `arch-decision-records` skill: captures architectural decisions in
  Y-Statement form, with three Rust-flavoured worked examples
  (typestate, verification-tool selection, unsafe alignment invariant).
- `proptest` skill: deep-dive guidance for property-based testing in
  Rust. Covers strategy design with `prop_compose!`, the filtering
  trap and its fix, `ProptestConfig` knobs (cases, shrink iterations,
  fork, timeout), regression-file discipline, the `proptest-derive`
  vs `test-strategy` choice, and `proptest-state-machine`. Ships an
  installation note, a strategy-pattern reference, and a
  self-contained Rust source example.
- `kani` skill: imported from `agent-helper-scripts` and rewired to
  install via `rust-prover-tools`. Replaces HNSW-specific examples with
  neutral graph-with-bidirectional-links harnesses; ships harness
  examples and a reference Rust source.
- `verus` skill: imported from `agent-helper-scripts` and rewired to
  install and run via `rust-prover-tools`. Replaces HNSW-specific
  examples with neutral `EdgeSpec`/`ItemSpec` proofs; ships worked
  proof examples, a reference Rust source, and an installation note.
- `rust-memory-and-state/references/encapsulation-and-raii.md`:
  ownership as architectural decoupling, RAII via `Drop`, and
  `Mutex`/`MutexGuard` as the canonical wireframe.
- `rust-unsafe-and-ffi/references/unsafecell-and-interior-mutability.md`:
  why `UnsafeCell` is the only sound foundation for shared mutation,
  the invariants wrappers must enforce, and common UB pitfalls.
- `rust-types-and-apis/references/misuse-resistant-apis.md`: typestate,
  newtype with hidden inner, anti-boolean-blindness with domain enums,
  API Guidelines checklist, and SemVer tooling.
- `rust-performance-and-layout/references/rigorous-benchmarking.md`:
  Tango paired benchmarking, iai-callgrind, open- versus closed-loop
  load models, tail-latency CDFs, and goodput.
- Skill manifest verification, imported from `agent-helper-scripts`:
  `make lint` now fails on a manifest a strict Agent Skills loader could
  not use. `skill-frontmatter-lint` runs `yamllint` over each manifest's
  frontmatter, `skill-manifest-validate` runs `skills-ref validate` over
  each skill directory, and `tests/test_skill_manifests.py` asserts the
  contract holds for every shipped skill and that `make lint` still
  enforces it.
- `skill-metadata-lint` and `tools/check_metadata.py`: the manifest gate
  now rejects a `metadata` key or value that is not a string, including
  YAML sequences and mappings. `skills-ref` coerces those shapes with
  `str(v)` instead of rejecting them, so without this target a manifest
  would reach consumers as a Python repr. `skill-manifest-check` runs
  the check ahead of schema validation, and
  `tests/test_skill_manifests.py` gains fixtures for each rejected
  shape, a manifest whose `name` disagrees with its directory, and a
  data contract over the relocated `metadata.globs` patterns.
- `tests/test_skill_manifests.py`: a contract test over the specialist
  invocation policy, which the manifest gate cannot see because
  `agents/openai.yaml` is not part of the Agent Skills manifest. Every
  skill but `rust-router` must ship the file with
  `policy.allow_implicit_invocation: false`, so no implicitly invocable
  specialist competes with the routing decision; a companion test fails
  if the router itself opts out, which would leave the catalogue
  reachable only by an explicit invocation. The developers' guide
  records the policy alongside what the suite covers, and `AGENTS.md`
  lists the file among the requirements for a change under `skills/`.

### Changed

- Rigour escalation rules ported from the `python-skill` catalogue.
  `rust-router` gains a testing hierarchy (named test, `rstest` table,
  lightweight `proptest`, structured or stateful `proptest`, Kani,
  Verus, with `cargo-mutants` beside and Miri below), a selection rubric,
  the "no selector ceremony for a clear invariant" pairing rule, and
  three escalation triggers. `rust-verification` gains "Before
  escalating", the question each tool answers, "What none of them
  establish", combination and cadence guidance, further red flags, and a
  `references/selection-matrix.md`. `proptest` gains "Start light" (the
  `#[case]` table that is a property in disguise), everyday property
  shapes, and an escalation ladder. `rust-unit-testing`, the routing
  matrix, and the users' guide point at the same hierarchy.
- `proptest/SKILL.md`: added the "Is a property test expected?" decision
  rule with the three accepted answers (land, defer with an issue, or
  write a scope statement), a strategy audit step before assertions,
  tautology and disjunction anti-patterns, the per-repository
  `.expect`/`prop_assert` lint policy note, `#[test]` inside `proptest!`,
  regression-file keying, `RandomState` determinism, and the sibling
  module layout.
- `kani/SKILL.md`: added the review bar (drive production code, no
  swallowed paths, prove both directions, shared driver, typed
  preconditions at the call site), the "`cfg(kani)` is a different build"
  checklist, the solver-cliff kernel-extraction pattern, the
  "measured intractable" protocol, the harness inventory duty, and the
  `prover-tools` project wiring pointer. `kani::cover!` joins the core
  concepts and the worked harness.
- `verus/SKILL.md`: added lemma decomposition as a review expectation,
  the restated-definition and unpropagated-axiom anti-patterns, the two
  production bridges and the refinement-lemma requirement, gating advice
  (Verus last, outside `make all`), lint policy in `verus/`, and the
  on-ramp pointer.
- `rust-verification/SKILL.md`: added "When reviewers expect
  verification": the estate trigger rule, the pre-merge check behaviour,
  and the three accepted responses.
- `rust-unsafe-and-ffi/SKILL.md`: added the missing-`UnsafeCell` red
  flag, a reference to the new interior-mutability material, and a
  cross-link to the `rust-verification` skill.
- `rust-types-and-apis/SKILL.md`: added the boolean-blindness red flag
  and a reference to the new misuse-resistant-APIs material.
- `rust-memory-and-state/SKILL.md`: added the encapsulation-and-RAII
  reference link.
- `rust-performance-and-layout/SKILL.md` and `benchmark-discipline.md`:
  added pointers to the new rigorous-benchmarking reference.
- `arch-crate-design/SKILL.md`: cross-linked the new `arch-supply-chain`
  skill from the packaging guidance.
- `rust-router/SKILL.md` and `references/routing-matrix.md`: added the
  `rust-unit-testing` focused skill and the `proptest` deep dive to routing
  entries.
- `rust-verification/SKILL.md` and `references/tool-selection.md`:
  routed into the new `proptest` deep dive alongside `kani` and
  `verus`.
- `docs/skill-catalogue-status.md` and `docs/users-guide.md`: listed
  `proptest` under the verification tier and described when to reach
  for it.
- Eleven `SKILL.md` manifests: the legacy top-level `globs` list moved
  into `metadata.globs` as a single comma-separated string. The Agent
  Skills schema admits only `name`, `description`, `license`,
  `allowed-tools`, `metadata`, and `compatibility`, and `skills-ref`
  rewrites sequence values with `str(v)`, so the pattern hints are
  preserved but re-encoded rather than dropped.

### Documentation

- `docs/execplans/advanced-encapsulation-and-verification.md`: the
  living ExecPlan governing this changelog block. Progress, surprises,
  and decisions are recorded inline as work advances.
- `docs/users-guide.md`: operator-facing guide covering catalogue
  installation, router invocation, and when to reach for the new
  verification, supply-chain, and decision-record skills. Linked from
  the README. Also explains that a manifest `name` is the discovery name,
  that the install copy performs no validation of its own, and that
  `make lint` is the contributor gate which validates every shipped
  manifest before it is published.
- `AGENTS.md`: commit-gate guidance for agents, covering the manifest
  contract and what to do when changing anything under `skills/`. Points
  tooling and dependency changes at the developers' guide.
- `docs/developers-guide.md`: prerequisites, the pinned `uv` dependency
  group, every `Makefile` target, the `SKILL_DIRS` override, the manifest
  contract, and what the test suite covers. Linked from the README.
