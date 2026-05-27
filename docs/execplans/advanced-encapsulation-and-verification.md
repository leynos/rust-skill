# Extend the Rust Skill Catalogue with Verification and Supply-Chain Skills

This ExecPlan (execution plan) is a living document. The sections
`Constraints`, `Tolerances`, `Risks`, `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work
proceeds.

Status: DRAFT (revised; see Revision note at end)

## Purpose / big picture

The current `skills/` catalogue covers the everyday Rust decision surface
(memory, types, errors, async, performance, unsafe, crate design, plus three
domain skills) and a focused `rust-unused-code` skill. It does not yet capture
the advanced "impeccable software" stance that the source document describes:
ownership as a coupling and decoupling lever, `UnsafeCell`-backed interior
mutability and `Drop`-driven RAII as the foundation of safe concurrency
wrappers, adversarial verification (Miri, sanitizers, property and mutation
testing, deterministic concurrency exploration via `loom`/`shuttle`/`turmoil`,
symbolic execution via Kani, deductive verification via Verus),
statistically rigorous benchmarking (paired benchmarking with Tango,
deterministic profiling with `iai-callgrind`, open-versus-closed load
topologies, tail-latency histograms), misuse-resistant APIs (typestate,
newtype, anti-boolean-blindness, API Guidelines, SemVer guardrails such as
`cargo-semver-checks` and `cargo-public-api`), and long-term viability
concerns (Architecture Decision Records in Y-Statement form, dependency
hygiene, decentralised auditing via `cargo-vet`).

In parallel, two existing skills outside this repository describe the deep
operating knowledge required to write Kani harnesses and Verus proofs. Those
skills currently live at
`/data/leynos/Projects/agent-helper-scripts/skills/kani/` and
`/data/leynos/Projects/agent-helper-scripts/skills/verus/`. This work imports
both skills into the catalogue and rewires their tool-installation guidance to
reference `https://github.com/leynos/rust-prover-tools`, which replaces the
ad hoc shell scripts (`install-verus.sh`, `run-verus.sh`) that the imported
skills currently carry.

After this work, a user asking the catalogue for help on any of those topics
should reach a compact first-class skill (or reference page on an existing
skill) instead of being told to consult external material. The router must
direct to the new material. A new `CHANGELOG.md` at the repository root, kept
in the [Common Changelog](https://common-changelog.org) style, must record the
additions. Existing documentation (`README.md`, `docs/skill-catalogue-status.md`,
the reduction execplan completion notes, and the routing-matrix reference)
must reflect the extended catalogue without bloating the README.

Success is observable when:

1. The catalogue contains the new first-class skills and reference material
   listed below, with each compact `SKILL.md` within the size budget the
   prior plan established and the two imported deep-dive skills (`kani`,
   `verus`) within the documented exception described in
   `Tolerances` below.
2. `skills/rust-router/SKILL.md` and `skills/rust-router/references/routing-matrix.md`
   route to the new skills for the corresponding questions, including
   routing into `kani` and `verus` from the verification skill.
3. The imported `kani` and `verus` skills no longer embed ad hoc shell
   scripts. Their installation and runner guidance points to
   `https://github.com/leynos/rust-prover-tools`.
4. A novice reader of `CHANGELOG.md` can see exactly which skills,
   references, and routing entries were added or changed in this release.
5. The README links to the new entry points without growing into a tutorial.
6. Repository-wide validation (`markdownlint-cli2` and `git diff --check`)
   continues to pass, mirroring the prior validation regime.

## Constraints

Hard invariants that must not be violated during this work:

- Stay within the catalogue shape established by
  `docs/execplans/reduced-skill-footprint.md`: one router, a small set of
  language skills, a small set of architecture and domain skills, and any
  focused single-topic skill (such as `rust-unused-code`). New skills must
  earn their place under the four criteria in that plan's "Design principles"
  section.
- Keep every newly authored compact `SKILL.md` short. The reduced-footprint
  plan's tolerance is roughly 3 KB unless a documented exception applies;
  longer comparison and example material must move into `references/`.
- The imported `kani` and `verus` skills are documented exceptions to the
  3 KB tolerance. Their value is procedural: writing harnesses and proofs
  is a high-stakes activity where worked examples and gotchas are the
  irreducible payload. Compress where the imported text restates basics
  the model already knows, and move the longest worked examples into
  `references/`, but do not pretend they will fit in 3 KB. See
  `Tolerances` for the cap.
- The imported skills must not retain `install-verus.sh`, `run-verus.sh`,
  or any other ad hoc tool-installation or runner script. Their imported
  content must direct the reader to
  `https://github.com/leynos/rust-prover-tools` for installation, version
  pinning, and proof execution.
- Use English only. Do not reintroduce multilingual trigger catalogues.
- Do not copy verbatim from the source brief except where a short code or
  invariant snippet is the only honest way to make the point.
- Do not modify `current-skills/` (it is legacy local input and must remain
  unstaged) or restructure unrelated parts of the repository.
- The README must remain a short orienting document. Detailed catalogue
  content belongs in `docs/` or in the relevant skill.
- The `CHANGELOG.md` must follow Common Changelog conventions: reverse
  chronological order, grouped entries (`Added`, `Changed`, `Fixed`,
  `Removed`, `Security`), human-readable prose, and dated releases (or an
  `Unreleased` section while the work is in progress).
- Do not start implementation work until the user approves this plan.

## Tolerances (exception triggers)

Stop and escalate if any of the following is true:

- Scope: the new tree would add more than five first-class skills
  (`rust-verification`, `arch-supply-chain`, `arch-decision-records`, plus
  the two imported deep-dive skills `kani` and `verus`), or grow the total
  committed `SKILL.md` footprint by more than roughly 100 percent over the
  current baseline. The wider tolerance reflects the deliberately heavy
  payload of the imported deep-dive skills.
- Size: any newly authored compact `SKILL.md` exceeds 4 KB, or any single
  reference file exceeds 8 KB, without a recorded justification. The
  imported `kani/SKILL.md` and `verus/SKILL.md` are capped at the size of
  their upstream copies plus any incremental edits required for the
  `rust-prover-tools` rewiring; if either exceeds that envelope after
  compression, stop and reconsider.
- Router pressure: the router cannot describe the new routes in fewer than
  six additional bullet lines without losing clarity.
- Naming overlap: the new skill names collide with existing skills or with
  near-future skills the user might reasonably expect (for example, a
  hypothetical `rust-testing` skill).
- Ambiguity: a section of the source document fits two existing skills
  equally well, and choosing one would meaningfully change the route. In
  that case, present the options before committing.
- Documentation churn: updating the README to mention every new skill would
  push it past one new short paragraph. If so, prefer linking to a
  catalogue page in `docs/` instead.
- Tooling drift: if a referenced tool (for example `cargo-vet`,
  `cargo-mutants`, `loom`, `shuttle`, `turmoil`, `kani`, `verus`,
  `iai-callgrind`, `tango`, or `rust-prover-tools`) has changed name,
  scope, or status since the source brief was written, stop and confirm
  the canonical name and URL before baking it into a skill.
- Import drift: if the upstream `kani` or `verus` skill at
  `/data/leynos/Projects/agent-helper-scripts/skills/` differs materially
  from the version inspected during this plan (for example, it has been
  rewritten or restructured), reconfirm the import scope before copying.

## Risks

- Risk: The new material drifts into tutorial mode and breaches the size
  budget.
  Severity: medium
  Likelihood: medium
  Mitigation: write each `SKILL.md` to the same compact shape used in
  `rust-memory-and-state` and `rust-async-and-concurrency` (trigger,
  working stance, decision surface, red flags, pointer to references).
  Move worked examples and tool-by-tool comparison into `references/`.

- Risk: The verification skill becomes a list of tool names without
  guidance on when to pick which.
  Severity: medium
  Likelihood: medium
  Mitigation: anchor the decision surface in the source document's
  classification (UB detection, input chaos, execution chaos, logic chaos,
  concurrency proofs, symbolic execution) and give one or two sentences per
  category about when to reach for it.

- Risk: Duplication with existing skills. For example, paired benchmarking
  could live in `rust-performance-and-layout`, and typestate/newtype
  guidance already partially exists in `rust-types-and-apis`.
  Severity: medium
  Likelihood: high
  Mitigation: extend existing skills with brief new references and
  routing notes when the topic is a natural deepening of an existing skill.
  Only create a new first-class skill when the topic is structurally
  separate (verification, supply chain, architectural decision records).

- Risk: Supply-chain guidance becomes vendor-specific or stale (for
  example, citing a particular registry tool that has since changed).
  Severity: low
  Likelihood: medium
  Mitigation: focus on the durable patterns (vetted dependency graphs,
  differential audits, decentralised trust, in-tree policy storage) and
  mention `cargo-vet`, `cargo-audit`, `cargo-deny`, and Dependabot/Renovate
  only as concrete instances of those patterns.

- Risk: The architectural decision record (ADR) skill steps into territory
  better covered by a general-purpose documentation skill.
  Severity: low
  Likelihood: medium
  Mitigation: keep the new content Rust-flavoured (typestate evolution,
  trait-bound tightening, public-API drift, unsafe invariants, runtime
  selection) and treat the Y-Statement format as a tool, not the subject.

- Risk: Imported `kani` and `verus` skills overlap with the new
  `rust-verification` skill and create routing ambiguity.
  Severity: medium
  Likelihood: high
  Mitigation: position `rust-verification` as the routing and selection
  layer (which technique for which failure mode), and treat `kani` and
  `verus` as deep operating manuals for users already inside one of those
  tools. The router and routing matrix must reflect this two-tier shape.

- Risk: The `rust-prover-tools` repository does not provide the exact
  install and runner surface the imported skills assume, so the rewiring
  leaves the skills in a half-broken state.
  Severity: medium
  Likelihood: medium
  Mitigation: Stage A.5 begins with a confirmation step that reads the
  `rust-prover-tools` repository and records the commands it exposes
  (install, run, version pinning). The skill rewrites then use those exact
  commands rather than paraphrased equivalents. If the surface is
  insufficient, stop and surface the gap before completing the rewrite.

- Risk: Imported references include language or patterns specific to the
  upstream project (for example, repository-relative paths such as
  `tools/verus/VERSION` or product-specific examples) that do not generalise.
  Severity: low
  Likelihood: high
  Mitigation: when porting, replace product-specific examples with neutral
  placeholders and reposition the project-layout discussion as an example
  pattern rather than a prescriptive recipe.

- Risk: README bloat. The current README is deliberately small.
  Severity: low
  Likelihood: medium
  Mitigation: add at most one short paragraph and one or two bullets to
  the README. Push the catalogue detail into `docs/skill-catalogue-status.md`
  (or a sibling page) and into the router.

## Progress

- [ ] Draft this ExecPlan and obtain user approval (revised draft includes
  the kani/verus import and the `rust-prover-tools` rewiring).
- [x] Stage 0: confirm tool names and current status (cargo-vet, cargo-mutants,
  loom, shuttle, turmoil, kani, verus, iai-callgrind, tango,
  cargo-semver-checks, cargo-public-api, and the install/run surface of
  `https://github.com/leynos/rust-prover-tools`). Record any naming
  surprises in `Surprises & Discoveries`. _Done: the `rust-prover-tools`
  surface is recorded below; other tool names match the source brief._
- [x] Stage A: extend existing skills with the smallest changes that fit
  (router routing entries; references in `rust-memory-and-state`,
  `rust-types-and-apis`, `rust-unsafe-and-ffi`, `rust-performance-and-layout`,
  `arch-crate-design`). _Done across commits 041d3ae, c5abe0b, 5d89231,
  adbd663, and 2300bd7._
- [x] Stage A.5: import the upstream `kani` and `verus` skills into
  `skills/kani/` and `skills/verus/`, rewire their installation and runner
  guidance to `rust-prover-tools`, drop the ad hoc shell scripts, compress
  where the imported text restates familiar Rust, and move long worked
  examples into `references/`. _Done in commits c0ddec8 (kani) and 679a230
  (verus); shell scripts not carried across._
- [ ] Stage B: add the new first-class skills (`rust-verification`,
  `arch-supply-chain`, and `arch-decision-records`; final names to be
  confirmed before file creation). `rust-verification` must explicitly
  route into the imported `kani` and `verus` skills.
- [ ] Stage C: create or update `CHANGELOG.md` in Common Changelog style with
  an `Unreleased` block summarising the additions, the imports, and the
  `rust-prover-tools` rewiring.
- [ ] Stage D: update `README.md` (one short paragraph and at most two
  bullets) and `docs/skill-catalogue-status.md` to mention the additions
  and the imports.
- [ ] Stage E: run the validation commands listed below and capture short
  transcripts under `Artifacts and notes`.

Each step must be committed individually with the commit gating described in
the repository's `AGENTS.md` (or the parent `CLAUDE.md`) where applicable.

## Surprises & Discoveries

Record discoveries here as work proceeds. Examples to capture:

- a tool from the source brief that has been renamed, archived, or
  superseded, and the canonical alternative,
- an existing skill that already covers a section of the source brief well
  enough that no new content is required,
- a place where the source brief and current Rust ecosystem practice diverge
  in a way that should influence the skill's recommendation.

### Stage 0: `rust-prover-tools` install/run surface

Confirmed from
[`rust_prover_tools/cli.py`](https://github.com/leynos/rust-prover-tools/blob/main/rust_prover_tools/cli.py)
on the `main` branch:

- The package exposes a single console script, `prover-tools`, with two
  command groups: `kani` and `verus`.
- Kani commands:
  - `prover-tools kani install` — installs the pinned Kani verifier, with
    optional `--repo-root`, `--version-file`, `--version`, `--no-setup`,
    and `--no-verify` flags.
  - `prover-tools kani check-version` — checks that the installed Kani
    matches the pinned version, with optional `--repo-root`,
    `--version-file`, `--expected-version`, and `--kani-command`
    (defaulting to `cargo kani`).
- Verus commands:
  - `prover-tools verus install` — installs the pinned Verus verifier,
    with optional `--repo-root`, `--version-file`, `--checksum-file`,
    `--target` (defaulting to `x86-linux` via `DEFAULT_TARGET`),
    `--install-dir`, and `--base-url` flags.
  - `prover-tools verus run --proof-file <path>` — runs Verus against a
    proof file, with optional `--repo-root`, `--version-file`,
    `--checksum-file`, `--install-dir`, `--target`, `--verus-bin`,
    `--no-ensure-toolchain`, `--no-install-missing`, and repeatable
    `--extra-arg` flags. Proof failures preserve the Verus exit code.
- Version pinning convention: file-based (`--version-file`,
  `--checksum-file`), defaulted relative to `--repo-root`. The cli.py
  module-level docstring gives the canonical example:
  `prover-tools verus run --proof-file verus/edge_harvest_proofs.rs`.
- Environment variable conventions: flags also read from
  `INPUT_*`-prefixed variables (for example, `INPUT_REPO_ROOT`,
  `INPUT_VERSION_FILE`, `INPUT_PROOF_FILE`, `INPUT_EXTRA_ARG`), and the
  legacy `KANI`, `VERUS_TARGET`, `VERUS_INSTALL_DIR`,
  `VERUS_PROOF_FILE`, and `VERUS_BIN` variables remain accepted.

The surface fully covers the install and run flows that
`install-verus.sh` and `run-verus.sh` previously performed, including
toolchain installation and checksum verification, so the imported `kani`
and `verus` skills can drop the shell-script fallback. The README of
`rust-prover-tools` is currently a Copier template stub, so the cli.py
module-level docstring (and its `Examples` section) is the canonical
reference for these commands until the README is fleshed out.

## Decision Log

Record significant decisions inline with the format used in the prior
execplan (numbered list with rationale). Anticipated decisions:

1. `rust-verification` is a router and selection layer; `kani` and `verus`
   are deep operating manuals. The default stance is to keep
   `rust-verification` compact (Miri, sanitizers, proptest, cargo-mutants,
   turmoil, shuttle, loom, and one-line routing into `kani` and `verus`
   for symbolic execution and deductive proofs respectively), and to keep
   the imported deep dives as separate first-class skills with their own
   size envelopes.
2. Whether to add a dedicated `arch-decision-records` skill or fold
   Y-Statement ADR guidance into `arch-crate-design`. The default stance is
   a separate small skill, because the audience and decision moment differ
   from packaging guidance.
3. Whether to add paired benchmarking and tail-latency guidance as a new
   `rust-benchmarking` skill or as an enlarged
   `rust-performance-and-layout` references set. The default stance is the
   references-set approach, because the new content deepens an existing
   decision surface rather than creating a new one.
4. Whether to add `cargo-vet` / SemVer / dependency-hygiene guidance as a
   new `arch-supply-chain` skill or as an `arch-crate-design` reference.
   The default stance is a new short skill, because the trigger ("auditing
   dependencies") is distinct from "should I split this into a crate?".
5. Whether to keep the imported `references/install-verus.sh` and
   `references/run-verus.sh` files in the catalogue. The default stance is
   to delete them. `rust-prover-tools` is the canonical replacement; the
   skill should not carry forked installation logic that will drift.
6. Whether to keep the imported example Rust files
   (`kani-harness-example.rs`, `verus-proof-example.rs`) as references.
   The default stance is to keep them, since worked harnesses and proofs
   are the irreducible payload for these skills, but to relocate any
   product-specific names into neutral placeholders during the port.

These defaults are recorded so the approver can challenge them before
implementation.

## Outcomes & Retrospective

To be completed after implementation. Compare the realised catalogue to the
purpose and tolerances above. Record any references that should have been
first-class skills (or vice versa) and any router entries that proved
confusing in practice.

## Context and orientation

The repository under `/data/leynos/Projects/rust-skill.worktrees/skill-refresh`
contains:

- `README.md`: a short orientation. It must stay short.
- `LICENSE`: MIT.
- `docs/skill-catalogue-status.md`: states that `skills/` is canonical and
  `current-skills/` is legacy local input that must not be committed.
- `docs/execplans/reduced-skill-footprint.md`: the prior execplan, now
  marked COMPLETE, describing why the catalogue was reduced and the size
  budget for each `SKILL.md`.
- `skills/rust-router/SKILL.md`: the entry-point skill. Routes by question
  type and lists pairing rules.
- `skills/rust-router/references/routing-matrix.md`: routing fallback when
  the first skill choice is not obvious.
- Language skills under `skills/`: `rust-memory-and-state`,
  `rust-types-and-apis`, `rust-errors`, `rust-async-and-concurrency`,
  `rust-performance-and-layout`, `rust-unsafe-and-ffi`.
- Architecture and domain skills: `arch-crate-design`,
  `domain-web-services`, `domain-cli-and-daemons`,
  `domain-embedded-and-iot`.
- Focused single-topic skill: `rust-unused-code` (note: it sits outside the
  language/architecture/domain trio and is allowed because it is a
  high-value, narrow topic).

There is no `CHANGELOG.md` yet. This work creates one.

The upstream skills to import live at:

- `/data/leynos/Projects/agent-helper-scripts/skills/kani/SKILL.md`
  (17,591 bytes) plus
  `/data/leynos/Projects/agent-helper-scripts/skills/kani/references/kani-harness-example.rs`.
- `/data/leynos/Projects/agent-helper-scripts/skills/verus/SKILL.md`
  (21,210 bytes) plus
  `/data/leynos/Projects/agent-helper-scripts/skills/verus/references/install-verus.sh`,
  `/data/leynos/Projects/agent-helper-scripts/skills/verus/references/run-verus.sh`,
  and
  `/data/leynos/Projects/agent-helper-scripts/skills/verus/references/verus-proof-example.rs`.

The two shell scripts encode a forked install-and-run workflow that this
work explicitly retires in favour of `rust-prover-tools` at
`https://github.com/leynos/rust-prover-tools`. They must not be copied into
this repository.

The source brief that motivates this work is the user prompt accompanying
this ExecPlan. Key topics in that brief that are not yet first-class in the
catalogue:

1. Ownership as architectural decoupling and borrowing as architectural
   coupling (deeper architectural framing than the current memory skill).
2. The interior-mutability story behind `Mutex`, including `UnsafeCell`,
   the `MutexGuard` co-structure, and `Drop`-driven release.
3. The full verification stack: Miri, LLVM sanitizers, property-based
   testing (`proptest`, `quickcheck`), mutation testing (`cargo-mutants`),
   deterministic chaos (`turmoil`, `shuttle`), exhaustive concurrency proofs
   (`loom`), and symbolic execution (`kani`).
4. Rigorous benchmarking: open versus closed system models, paired
   benchmarking (`tango`), deterministic profiling (`iai-callgrind`), tail
   latency and goodput.
5. Misuse-resistant APIs: typestate, newtype, anti-boolean-blindness,
   selected Rust API Guidelines (C-SEALED, C-NEWTYPE-HIDE, C-SMART-PTR,
   C-STRUCT-PRIVATE), `cargo-semver-checks` and `cargo-public-api`.
6. Architecture Decision Records in the Y-Statement format.
7. Dependency hygiene and supply-chain auditing: dependency stagnation,
   automated update bots, isolating volatile dependencies behind internal
   adapters, `cargo-vet` (incremental onboarding, differential audits,
   decentralised trust, in-tree policy storage), and adjacent tools such as
   `cargo-audit` and `cargo-deny`.

## Plan of work

Stages execute in order. Each ends with the validation commands listed
later in this plan.

### Stage 0: tool-naming confirmation (no file changes)

Confirm canonical names, repository or crate locations, and current status
of: `cargo-vet`, `cargo-mutants`, `cargo-audit`, `cargo-deny`,
`cargo-semver-checks`, `cargo-public-api`, `loom`, `shuttle`, `turmoil`,
`kani`, `verus`, `miri`, `iai-callgrind`, and `tango` (or its successor
name). Record any name changes in `Surprises & Discoveries`. Defer to
canonical Rust ecosystem references; do not invent or guess tool URLs.

Also inspect `https://github.com/leynos/rust-prover-tools` and record:

- the canonical install command (or scripted entry point) that replaces
  `install-verus.sh`,
- the canonical proof-runner command that replaces `run-verus.sh`,
- whether the same tooling covers Kani as well as Verus,
- any version-pinning convention the tool expects (for example, a
  configuration file or environment variable).

If any of those are unclear or absent, stop and surface the gap before
proceeding to Stage A.5.

Exit when each tool name used in the new and imported skills is confirmed
and the ExecPlan reflects any corrections.

### Stage A: extend existing skills (smallest changes first)

Each change adds at most one bullet to the working stance or decision
surface, one or two new red flags, and one new reference link. Stay within
the existing size budget.

1. `skills/rust-memory-and-state/SKILL.md`

   Add a brief reference pointer to a new
   `references/encapsulation-and-raii.md` page that covers ownership as
   architectural decoupling, borrowing as architectural coupling, and the
   `Mutex`/`MutexGuard`/`Drop` lifecycle as the canonical RAII pattern.
   The body of the new page (not the SKILL itself) carries the detail.

2. `skills/rust-unsafe-and-ffi/SKILL.md`

   Add a brief reference pointer to a new
   `references/unsafecell-and-interior-mutability.md` page that explains the
   role of `UnsafeCell`, why aliasing rules require it for safe interior
   mutability, the `noalias` interaction with LLVM, and the small list of
   well-known undefined-behaviour pitfalls. Cross-reference Miri and loom
   from the new verification skill (Stage B).

3. `skills/rust-types-and-apis/SKILL.md`

   Add a brief reference pointer to a new
   `references/misuse-resistant-apis.md` page covering typestate,
   newtypes, anti-boolean-blindness, the relevant Rust API Guidelines
   identifiers (C-SEALED, C-NEWTYPE-HIDE, C-SMART-PTR, C-STRUCT-PRIVATE),
   and SemVer tooling (`cargo-semver-checks`, `cargo-public-api`). Also
   add a red flag for boolean blindness in public APIs.

4. `skills/rust-performance-and-layout/SKILL.md`

   Add a brief reference pointer to a new
   `references/rigorous-benchmarking.md` page covering paired benchmarking
   (Tango), deterministic profiling (`iai-callgrind`), open-versus-closed
   load topologies, goodput, and tail latency / CDFs. Also extend
   `references/benchmark-discipline.md` with a short pointer to the new
   page rather than duplicating content.

5. `skills/arch-crate-design/SKILL.md`

   Add a single bullet under "Packaging and release guidance" pointing at
   the new supply-chain skill (Stage B) and at SemVer tooling. Avoid
   restating supply-chain content here.

### Stage A.5: import `kani` and `verus` from agent-helper-scripts

Copy the upstream skills into the catalogue and adapt them to this
repository's conventions.

1. Create `skills/kani/SKILL.md` from
   `/data/leynos/Projects/agent-helper-scripts/skills/kani/SKILL.md`.
   Adaptations:

   - Replace the standalone "Installation" guidance ("Install Kani via
     Cargo: `cargo install --locked kani-verifier && cargo kani setup`")
     with a short pointer to `rust-prover-tools`, naming the install
     command surface confirmed in Stage 0. Retain a fallback line
     mentioning the upstream `cargo install kani-verifier` route for
     readers who cannot use `rust-prover-tools`.
   - Replace product-specific harness examples (the HNSW graph
     reconciliation and eviction examples) with neutral placeholders or
     move the unedited code into
     `skills/kani/references/harness-examples.md` (text wrapped) so the
     `SKILL.md` body can shrink. Keep at least one passing positive
     example and at least one anti-pattern example inline.
   - Trim sections that restate Rust basics the catalogue already
     assumes (for example, paragraph-length explanations of nondeterministic
     inputs or assertions). Aim to bring the body under the imported
     skill's original size after compression; record the achieved size
     in `Artifacts and notes`.
   - Update the "Where Kani fits in the verification spectrum" diagram to
     link explicitly to `rust-verification` (added in Stage B) as the
     overall routing entry point.
   - Copy
     `/data/leynos/Projects/agent-helper-scripts/skills/kani/references/kani-harness-example.rs`
     to `skills/kani/references/kani-harness-example.rs`, renaming any
     product-specific symbols. Confirm the file remains syntactically
     valid Rust source even though it is not compiled in this repository.

2. Create `skills/verus/SKILL.md` from
   `/data/leynos/Projects/agent-helper-scripts/skills/verus/SKILL.md`.
   Adaptations:

   - Replace the "Installation and toolchain" section. The new section
     must direct the reader to `https://github.com/leynos/rust-prover-tools`
     for installation, version pinning, checksum handling, and proof
     execution. Remove the references to `tools/verus/VERSION`,
     `tools/verus/SHA256SUMS`, `references/install-verus.sh`, and
     `references/run-verus.sh`.
   - Rewrite the "Running proofs" guidance to use the
     `rust-prover-tools` runner surface confirmed in Stage 0 instead of
     the four-step pseudo-code (resolve binary; parse toolchain; install
     toolchain; execute proofs).
   - Trim "Core concepts" entries that restate basic Rust syntax. Keep
     the Verus-specific material (modes, `verus!` macro, requires/ensures,
     spec/proof functions, triggers, `assert ... by`).
   - Replace product-specific examples (HNSW edge canonicalisation,
     extraction lemma chains) with neutral placeholders. Move long
     worked examples into `skills/verus/references/proof-examples.md`.
   - Copy
     `/data/leynos/Projects/agent-helper-scripts/skills/verus/references/verus-proof-example.rs`
     to `skills/verus/references/verus-proof-example.rs`, renaming any
     product-specific symbols.
   - Do **not** copy
     `/data/leynos/Projects/agent-helper-scripts/skills/verus/references/install-verus.sh`
     or `.../run-verus.sh`. Their replacement is `rust-prover-tools`.
   - Update the front matter `description:` so it makes the skill's
     trigger discoverable without relying on the deep-dive body. The
     existing upstream description ("Write and maintain Verus deductive
     proofs for Rust code...") is acceptable; lengthen only if necessary.

3. Adjust each imported `SKILL.md`'s front matter to match this
   repository's existing convention. Specifically:

   - Keep `name:` matching the directory name (`kani`, `verus`).
   - Keep `description:` as a single line that names triggers an agent
     can match against.
   - Do **not** add `globs:` unless the upstream skill already had them;
     the deep-dive skills are intentionally invoked by name, not by file
     pattern.

4. Record the final byte sizes of `skills/kani/SKILL.md` and
   `skills/verus/SKILL.md` after compression in `Artifacts and notes`.

5. Add a brief deprecation pointer in
   `skills/kani/references/installation-note.md` and
   `skills/verus/references/installation-note.md` (one short page each)
   that explicitly states: "The previous install and runner scripts have
   been replaced by `rust-prover-tools`. See
   `https://github.com/leynos/rust-prover-tools` for the current
   workflow." This makes the change discoverable for readers who arrive
   from the upstream catalogue.

### Stage B: add new first-class skills

Default choices (subject to Decision Log entry 1, 2, and 4):

1. `skills/rust-verification/SKILL.md`

   Trigger: load when correctness under adversarial or concurrent
   conditions is the real question, not happy-path testing.

   Working stance: assert assumptions; test error returns explicitly;
   pick the verification tool that matches the failure mode; do not run
   exhaustive tools (loom, kani, verus) over whole applications.

   Decision surface: undefined behaviour (Miri, sanitizers); input chaos
   (proptest, quickcheck); execution chaos (turmoil, shuttle); logic
   chaos (cargo-mutants); concurrency proofs (loom); symbolic execution
   (kani — load the `kani` skill for harness authoring); deductive
   proofs over unbounded domains (verus — load the `verus` skill for
   proof authoring). One sentence per category about when to reach for
   it.

   Routing rule: this skill is the entry point for "which verification
   technique?". Once the choice is "Kani" or "Verus", route directly to
   the imported deep-dive skill rather than restating its content here.

   Red flags: error paths are untested; concurrent code is "tested" only
   by running it; benchmarks are used as correctness checks; loom or
   kani or verus is invoked on entire applications rather than on small
   primitives.

   Pointer to references: `references/tool-selection.md` and
   `references/deterministic-chaos.md`.

2. `skills/arch-supply-chain/SKILL.md`

   Trigger: load when the question is what dependencies should enter the
   build graph, how they should be audited, or how the project should keep
   up with upstream changes.

   Working stance: track dependency hygiene as engineering work, not as
   incident response; isolate volatile dependencies behind internal
   adapters; vet new dependencies before they enter the graph; treat
   public trait implementations on foreign types as a SemVer commitment to
   the foreign crate.

   Decision surface: when to add a new dependency; when to wrap a
   volatile one; when to audit (cargo-vet, cargo-audit, cargo-deny); how
   to handle SemVer-breaking upgrades (cargo-semver-checks,
   cargo-public-api); how to run differential audits.

   Red flags: dependencies drift years behind their stable versions; a
   single dependency dictates the SemVer story of the entire crate;
   audits are deferred to "when the vulnerability shows up"; a foreign
   trait implementation on a public type forces every consumer to take a
   major upgrade.

   Pointer to references: `references/cargo-vet-and-trust.md` and
   `references/dependency-hygiene.md`.

3. `skills/arch-decision-records/SKILL.md`

   Trigger: load when an architectural decision (or its retirement) needs
   to be captured so future maintainers can revisit it without re-running
   the original investigation.

   Working stance: capture the context, concern, decision, alternatives,
   quality goal, and accepted downside; record what was deliberately not
   done; revisit ADRs when the context shifts; keep ADRs short and
   review-able.

   Decision surface: Y-Statement ADR (default) versus longer formats;
   one ADR per decision versus a rolling design log; storing ADRs
   alongside the code versus in a separate documentation tree.

   Red flags: decisions exist only in chat logs or pull-request
   descriptions; an ADR repeats what the code already shows; an ADR has
   no "alternatives discounted" section; an ADR has no concrete
   downside.

   Pointer to references: `references/y-statement-template.md`.

Hold the size budget. If any of these grows beyond about 3 KB, move
content into references before promoting it.

### Stage C: create `CHANGELOG.md`

Create `CHANGELOG.md` at the repository root using Common Changelog
conventions. Initial structure:

~~~markdown
# Changelog

All notable changes to this skill catalogue are documented in this file.

The format is based on [Common Changelog](https://common-changelog.org).

## [Unreleased]

### Added

- `rust-verification` skill covering undefined-behaviour detection,
  property-based and mutation testing, deterministic concurrency
  exploration, and the routing entry points into the deep-dive `kani`
  and `verus` skills.
- `kani` skill imported from the agent-helper-scripts catalogue and
  rewired to install through
  [`rust-prover-tools`](https://github.com/leynos/rust-prover-tools).
- `verus` skill imported from the agent-helper-scripts catalogue and
  rewired to install and run through
  [`rust-prover-tools`](https://github.com/leynos/rust-prover-tools).
- `arch-supply-chain` skill covering dependency hygiene, SemVer tooling,
  and decentralised audit workflows.
- `arch-decision-records` skill covering Y-Statement architectural
  decision records and when to revisit them.
- New reference pages: `rust-memory-and-state/references/encapsulation-and-raii.md`,
  `rust-unsafe-and-ffi/references/unsafecell-and-interior-mutability.md`,
  `rust-types-and-apis/references/misuse-resistant-apis.md`,
  `rust-performance-and-layout/references/rigorous-benchmarking.md`.

### Changed

- `rust-router` now routes verification, supply-chain, and
  architectural-decision questions to the new skills, and routes
  Kani-specific and Verus-specific questions directly to the imported
  deep-dive skills.
- `rust-types-and-apis` highlights boolean blindness as a red flag.
- `rust-memory-and-state`, `rust-unsafe-and-ffi`, and
  `rust-performance-and-layout` link to their new reference pages.

### Removed

- The ad hoc `install-verus.sh` and `run-verus.sh` scripts that the
  upstream `verus` skill carried. Installation and proof execution now
  flow through `rust-prover-tools`.

### Documentation

- README adds a short pointer to the verification, supply-chain, and
  decision-records skills, and notes the new `kani` and `verus`
  deep-dive skills.
- `docs/skill-catalogue-status.md` records the new first-class skills
  and the imports.
~~~

If prior tags or releases exist, retain them and add the `Unreleased`
section above them. Release-numbering decisions are out of scope unless
the user requests a tag.

### Stage D: update README and catalogue status

In `README.md`:

- Add one short paragraph under "Features" or "Learn more" describing
  the verification, supply-chain, and decision-records additions.
- Add at most one or two bullets under "Learn more" linking to the new
  skills.
- Do not expand the README beyond that.

In `docs/skill-catalogue-status.md`:

- Add a short list of the new first-class skills and the new reference
  pages so the catalogue map remains discoverable.

In `skills/rust-router/SKILL.md` and
`skills/rust-router/references/routing-matrix.md`:

- Add route entries for "verification, chaos testing, Miri, loom",
  routed to `rust-verification`; for "Kani harnesses, bounded model
  checking, `#[kani::proof]`", routed directly to `kani`; for "Verus
  proofs, deductive verification, `spec fn`, `proof fn`, triggers",
  routed directly to `verus`; for "dependency audits, supply chain,
  cargo-vet, SemVer tooling", routed to `arch-supply-chain`; and for
  "architecture decisions, ADR, Y-Statement", routed to
  `arch-decision-records`. Use compact wording that matches the existing
  style.
- Update pairing rules where needed (for example, pair
  `rust-verification` with `rust-unsafe-and-ffi` for soundness work;
  note that `kani` and `verus` pair well with `rust-unsafe-and-ffi` and
  `rust-types-and-apis` respectively when the proof obligation is unsafe
  invariants or pure logic on typed domains).

### Stage E: validation

Run, in order:

~~~plaintext
git status
git diff --stat
find skills -name SKILL.md -print0 | xargs -0 wc -c | sort -n
rg -n "Layer 1|Layer 2|Layer 3|Trace Up|Trace Down|Thinking Prompt" skills
rg -n "[一-龥]" skills
find skills -type f \( -name 'install-verus.sh' -o -name 'run-verus.sh' \)
rg -n "rust-prover-tools" skills/kani skills/verus
markdownlint-cli2 'docs/**/*.md' 'skills/**/*.md' 'README.md' 'CHANGELOG.md'
git diff --check
~~~

Acceptance:

- No `SKILL.md` introduces the removed scaffolding.
- No non-English trigger text is reintroduced.
- The newly authored compact `SKILL.md` files are within the size budget;
  the imported `kani/SKILL.md` and `verus/SKILL.md` are within the
  documented exception in `Tolerances`.
- No file under `skills/` is named `install-verus.sh` or `run-verus.sh`.
- `rg -n 'rust-prover-tools' skills` returns a match in both
  `skills/kani/` and `skills/verus/`.
- `markdownlint-cli2` reports no issues across the new and updated files.
- `git diff --check` reports no whitespace issues.

## Concrete steps

Execute each stage in its own commit (or a small commit per affected
skill within a stage), gating each commit per repository policy. Use
short, descriptive commit messages: for example, `Add rust-verification
skill` or `Link rust-memory-and-state to encapsulation-and-raii reference`.

Suggested command outline:

~~~plaintext
# Stage A example for one skill
$EDITOR skills/rust-memory-and-state/SKILL.md
$EDITOR skills/rust-memory-and-state/references/encapsulation-and-raii.md
markdownlint-cli2 'skills/rust-memory-and-state/**/*.md'
git add skills/rust-memory-and-state
git commit -m "Add encapsulation-and-RAII reference to rust-memory-and-state"

# Stage B example for one skill
mkdir -p skills/rust-verification/references
$EDITOR skills/rust-verification/SKILL.md
$EDITOR skills/rust-verification/references/tool-selection.md
$EDITOR skills/rust-verification/references/deterministic-chaos.md
markdownlint-cli2 'skills/rust-verification/**/*.md'
git add skills/rust-verification
git commit -m "Add rust-verification skill"

# Stage C example
$EDITOR CHANGELOG.md
markdownlint-cli2 CHANGELOG.md
git add CHANGELOG.md
git commit -m "Add CHANGELOG.md following Common Changelog conventions"

# Stage D example
$EDITOR README.md
$EDITOR docs/skill-catalogue-status.md
$EDITOR skills/rust-router/SKILL.md
$EDITOR skills/rust-router/references/routing-matrix.md
markdownlint-cli2 'docs/**/*.md' 'skills/rust-router/**/*.md' 'README.md'
git add README.md docs/skill-catalogue-status.md skills/rust-router
git commit -m "Route to new verification, supply-chain, and ADR skills"

# Stage E (final validation)
markdownlint-cli2 'docs/**/*.md' 'skills/**/*.md' 'README.md' 'CHANGELOG.md'
git diff --check
git log --oneline -n 10
~~~

Update this section as work proceeds. Replace illustrative commands with
the real ones once executed.

## Validation and acceptance

Quality criteria for "done":

- Tests: not applicable; this repository contains documentation only.
- Lint: `markdownlint-cli2 'docs/**/*.md' 'skills/**/*.md' 'README.md'
  'CHANGELOG.md'` reports no errors.
- Whitespace: `git diff --check` reports no issues.
- Structural: the validation `rg` commands above return no matches.
- Behavioural: a reader who asks "how do I verify this concurrent code?",
  "how do I keep my dependencies safe?", or "where do I record this
  architectural decision?" follows the router to the new skill in a
  single hop.
- Documentation: the README mentions the new skills in one short
  paragraph and at most two new bullets, with detail living in
  `docs/skill-catalogue-status.md` and the skills themselves.
- Changelog: `CHANGELOG.md` records every added or changed file group
  under the `Unreleased` block in Common Changelog form.

Quality method:

- Manual review of the router and routing matrix.
- Manual review of each new `SKILL.md` against the compact shape used by
  the existing language skills.
- The validation command block above.

## Idempotence and recovery

All work is documentation only. Steps are safe to re-run:

- Re-running `markdownlint-cli2` does not change files unless `--fix` is
  passed; do not pass `--fix` blindly across the catalogue.
- Re-running edits with the same content is a no-op; Git will report no
  change.
- If a stage's commit needs to be revised, prefer a new commit over an
  amend (per repository policy in `CLAUDE.md`).
- If a new skill turns out to overlap with an existing skill, prefer
  collapsing the new content into the existing skill's references over
  shipping two skills with overlapping descriptions.

## Artifacts and notes

Record short transcripts here after each stage. Expected snippets:

~~~plaintext
# After Stage E
$ find skills -name SKILL.md -print0 | xargs -0 wc -c | sort -n | tail -n 5
... (sizes of the largest SKILL.md files, including the new ones)

$ markdownlint-cli2 'docs/**/*.md' 'skills/**/*.md' 'README.md' 'CHANGELOG.md'
markdownlint-cli2 ...
Finding: ... 0 errors

$ git diff --check
(no output)
~~~

## Interfaces and dependencies

This work changes no code interfaces. The "interfaces" affected are
documentation contracts:

- The router's routing entries must name the new skills exactly as the
  new `SKILL.md` `name:` fields declare them.
- The `description:` field in each new `SKILL.md` must be specific enough
  that an agent can choose the skill without opening another one first
  (matching the discoverability criterion from the prior execplan).
- The Common Changelog conventions (`Unreleased`, `Added`, `Changed`,
  `Fixed`, `Removed`, `Security`, with reverse chronological versioned
  sections once releases exist) define the `CHANGELOG.md` contract.

## Revision note

Initial draft created in this branch.

Revision 1 (same drafting session): added the import of the upstream
`kani` and `verus` skills from
`/data/leynos/Projects/agent-helper-scripts/skills/` and the replacement
of the ad hoc install and runner scripts with
`https://github.com/leynos/rust-prover-tools`. The change affects
`Purpose / big picture`, `Constraints`, `Tolerances`, `Risks`,
`Progress`, `Decision Log`, `Context and orientation`, the `Plan of
work` (new Stage A.5 and revised Stage B), the `CHANGELOG.md` template
in Stage C, the router updates in Stage D, and the validation command
list and acceptance criteria in Stage E. No work has been executed yet;
implementation remains gated on user approval.

Future revisions to this plan must record what changed, why, and how it
affects the remaining work, per the execplans skill.
