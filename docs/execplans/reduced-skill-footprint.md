# Overhaul the Rust Skill Catalogue into a Smaller, Sharper `skills/` Tree

This ExecPlan (execution plan) is a living document. The sections
`Constraints`, `Tolerances`, `Risks`, `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work
proceeds.

Status: COMPLETE

## Purpose / big picture

The current Rust skill set in `current-skills/` is too large, too repetitive,
and too eager to explain Rust from first principles even when the model already
knows the basics. The overhaul should produce a smaller catalogue in `skills/`
that is easier to load, easier to route, and more likely to improve real Rust
work instead of consuming context budget.

Success is visible in three ways. First, the default Rust route should become
obvious: one router/framing skill, five to seven compact language skills, and
three to five compact domain or architecture skills. Second, the new skills
should keep only high-value prompts, patterns, and lesser-known traps, while
dropping explanations the model already carries. Third, the new tree should be
small enough that loading one or two skills helps with the work instead of
competing with it.

## Repository orientation

This repository currently contains almost nothing except the source material to
be reduced. The present catalogue lives under `current-skills/`. The new
catalogue will live under `skills/`. There is no existing `docs/execplans/`
tree besides this plan, so future work must create the new `skills/` tree from
scratch rather than assume a migration framework already exists.

The current branch name is `reduced-skill-footprint`, so the canonical plan
path is `docs/execplans/reduced-skill-footprint.md`.

## Baseline evidence

The present footprint is large enough that reduction must be structural rather
than editorial.

```plaintext
$ find current-skills -name SKILL.md -print0 | xargs -0 wc -c | tail -n 1
194029 total

$ wc -c current-skills/rust/SKILL.md current-skills/rust-router/SKILL.md
21031 current-skills/rust/SKILL.md
 8104 current-skills/rust-router/SKILL.md

$ wc -c current-skills/rust-call-graph/SKILL.md \
       current-skills/rust-code-navigator/SKILL.md \
       current-skills/rust-deps-visualizer/SKILL.md \
       current-skills/rust-refactor-helper/SKILL.md \
       current-skills/rust-symbol-analyzer/SKILL.md \
       current-skills/rust-trait-explorer/SKILL.md \
       current-skills/meta-cognition-parallel/SKILL.md | tail -n 1
34779 total
```

The repeated surface is also easy to verify. Many files repeat the same
headings and the same three-layer framing:

```plaintext
$ rg -n \
  "Layer 1|Layer 2|Layer 3|Trace Down|Trace Up|Core Question|Thinking Prompt" \
  current-skills
current-skills/m01-ownership/SKILL.md
current-skills/m02-resource/SKILL.md
current-skills/m03-mutability/SKILL.md
current-skills/m04-zero-cost/SKILL.md
current-skills/m05-type-driven/SKILL.md
current-skills/m06-error-handling/SKILL.md
current-skills/m07-concurrency/SKILL.md
current-skills/m09-domain/SKILL.md
current-skills/m10-performance/SKILL.md
current-skills/m11-ecosystem/SKILL.md
current-skills/m12-lifecycle/SKILL.md
current-skills/m13-domain-error/SKILL.md
current-skills/m14-mental-model/SKILL.md
current-skills/m15-anti-pattern/SKILL.md
current-skills/domain-*
current-skills/rust-router/SKILL.md
```

The current set also mixes Rust guidance with tool wrappers and multilingual
trigger catalogues. Those make the catalogue larger without making the Rust
advice better.

## Constraints

- Keep the overhaul specific to Rust. Do not turn this into a generic agent
  skill library.
- Use English only in the new skills. Remove Chinese and other non-English
  trigger text from the new catalogue.
- Do not quote the current skills verbatim in the new skills, except where a
  code example is the irreducible way to show a Rust construct or pitfall.
- Preserve genuinely useful strategy bundles and non-obvious language traps,
  even if the underlying facts are familiar.
- Remove duplicated tool-specific Rust skills when the same capability is
  already better handled by general tools such as `leta`.
- Keep new `SKILL.md` files short enough that loading one or two is cheap.
  Longer examples, comparisons, or reference material must move into
  `references/`.
- Do not start implementation until the user approves this plan.

## Tolerances (exception triggers)

- Scope: if the proposed replacement tree grows beyond one router, seven
  language skills, and five domain or architecture skills, stop and trim
  before continuing.
- Size: if any new `SKILL.md` exceeds roughly 3 KB without a strong,
  documented reason, stop and move material into `references/`.
- Migration churn: if preserving a current skill requires more than a simple
  merge, rename, or extraction into `references/`, prefer dropping it unless
  the value is clear and documented.
- Ambiguity: if a current skill appears partly useful but the useful portion
  cannot be stated clearly in a sentence or two, stop and decide whether it is
  really reusable knowledge or just verbose filler.
- Tool overlap: if a proposed Rust skill mainly instructs use of `LSP`, `Read`,
  `Glob`, `Grep`, or similar tooling rather than Rust reasoning, stop and move
  it out of the Rust catalogue.

## Risks

- Risk: Over-pruning removes small but real prompts that help the model
  remember uncommon Rust edges.
  Severity: medium
  Likelihood: medium
  Mitigation: classify every current skill as drop, merge, keep as reference,
  or keep as first-class skill, with a sentence of rationale.

- Risk: The new skills become concise but bland, losing the mindset value the
  user asked to preserve.
  Severity: medium
  Likelihood: medium
  Mitigation: give every first-class skill a short "working stance" block with
  four to six concrete behavioural prompts, not motivational prose.

- Risk: Tool-wrapper skills survive because they are easy to port even though
  they do not belong in a Rust language set.
  Severity: medium
  Likelihood: high
  Mitigation: explicitly separate Rust reasoning skills from tool-use guidance
  and default to general tool skills for navigation/refactoring.

- Risk: Domain coverage becomes too narrow if the catalogue keeps only the
  most common domains.
  Severity: low
  Likelihood: medium
  Mitigation: keep rare or specialised material as dormant references or
  future follow-up work instead of forcing it into the first pass.

## Design principles for the new catalogue

The new tree should assume the model already knows normal Rust. A skill should
earn its bytes by doing one of four things:

1. It sharpens action under pressure. Examples: how to decide between owning,
   borrowing, cloning, interior mutability, async task ownership, or a safe
   wrapper around unsafe code.
2. It assembles patterns that are easy to forget in the moment. Examples:
   choosing between generics and trait objects, error layering across library
   and binary boundaries, or state and cancellation design for async systems.
3. It carries less obvious language or ecosystem facts. Examples:
   pinning, variance pressure from pointer types, FFI soundness obligations,
   `Send`/`Sync` consequences, or public API stability trade-offs.
4. It frames the work in a way that changes the next decision immediately.
   Examples: "model invariants first", "measure before optimising", or "prefer
   one owner and many readers until the data says otherwise".

Everything else should either vanish or move behind progressive disclosure in
`references/`.

## Catalogue of what to eliminate, merge, or preserve

### Remove from the first-class catalogue

The following categories are mostly restating knowledge the model already has,
or they are thin wrappers over general tooling rather than Rust expertise:

1. `rust/SKILL.md`

   This is a 21 KB omnibus ruleset. It is too large to load routinely and too
   broad to provide a sharp frame for a specific Rust task. Keep only the best
   unusual rules as reference notes; do not keep this as a first-class skill.

2. Tool-wrapper skills:
   `rust-call-graph`, `rust-code-navigator`, `rust-deps-visualizer`,
   `rust-refactor-helper`, `rust-symbol-analyzer`, `rust-trait-explorer`,
   `meta-cognition-parallel`

   These are not really Rust language skills. Most are instructions for using
   navigation or refactoring tools, and one is a meta-analysis pattern that
   belongs nowhere near a compact Rust default loadout. Replace them with a
   short note in the router saying to use the general `leta` skill for code
   navigation and refactoring.

3. Repeated coaching scaffolding

   Repeated sections such as `Core Question`, `Thinking Prompt`, `Trace Up`,
   `Trace Down`, and the three-layer taxonomy appear across many skills. Keep
   only the minimum framing needed to route and act. Do not restate the same
   scaffold in every file.

4. Multilingual trigger lists

   The new catalogue should be English only. The present multilingual keyword
   lists increase surface area and distract from the actionable content.

### Merge into fewer language skills

These current skills contain useful material, but not enough distinct value to
survive as separate top-level skills:

1. Merge `m01-ownership`, `m02-resource`, `m03-mutability`, and `m12-lifecycle`
   into a single memory-and-state skill.

   The useful part is the decision surface around ownership shape, aliasing,
   lifetimes, interior mutability, RAII, and state handoff. The repeated
   explanations of what `Box`, `Rc`, `Arc`, `RefCell`, and lifetimes are can be
   compressed heavily.

2. Merge `m04-zero-cost`, `m05-type-driven`, and parts of `m11-ecosystem` into
   a types-and-API-design skill.

   The high-value material is how to choose between generics, trait objects,
   newtypes, typestate, sealed traits, and conversion boundaries. The basic
   "what is a trait" or "what is a generic" material can be removed.

3. Merge `m09-domain`, `m13-domain-error`, and `m15-anti-pattern` into a
   design-and-failure skill, or fold their strongest parts into the router plus
   the error and API-design skills.

   The worthwhile part is boundary thinking, invariant-first modelling, and
   failure classification. The life-coach surface and generic "think about the
   domain" prose should go.

4. Keep `m06-error-handling` as a first-class language skill, but shrink it to
   library-versus-binary choices, context propagation, panic boundaries, and
   error shape selection.

5. Keep `m07-concurrency` as a first-class language skill, but focus it on
   ownership across tasks, cancellation, blocking boundaries, runtime concerns,
   and shared-state trade-offs instead of re-explaining `async` syntax.

6. Keep `m10-performance` as a first-class language skill, but strip generic
   performance advice that does not depend on Rust.

### Preserve as first-class because the subject is genuinely easy to miss

1. `unsafe-checker`

   Unsafe Rust has special obligations and benefits from a dedicated skill.
   Remove the novelty formatting and keep a compact soundness checklist,
   wrapper-first guidance, and the few irreducible examples that explain
   invariants better than prose.

2. A small router or framing skill

   The router is useful, but only if it stops trying to be a theory of mind.
   It should route by question type, name the right skill quickly, and load a
   short working stance that improves the next Rust decision.

## Proposed first-class skills in `skills/`

This plan recommends one router, six language skills, and four domain or
architecture skills.

```plaintext
skills/
├── rust-router/
│   ├── SKILL.md
│   └── references/
│       └── routing-matrix.md
├── rust-memory-and-state/
│   ├── SKILL.md
│   └── references/
│       ├── borrow-and-own-patterns.md
│       ├── interior-mutability.md
│       └── lifecycle-and-raii.md
├── rust-types-and-apis/
│   ├── SKILL.md
│   └── references/
│       ├── generics-vs-dyn.md
│       ├── newtypes-and-typestate.md
│       └── public-api-boundaries.md
├── rust-errors/
│   ├── SKILL.md
│   └── references/
│       ├── library-vs-binary-errors.md
│       └── retry-cancel-classification.md
├── rust-async-and-concurrency/
│   ├── SKILL.md
│   └── references/
│       ├── send-sync-checklist.md
│       ├── task-ownership.md
│       └── blocking-and-backpressure.md
├── rust-performance-and-layout/
│   ├── SKILL.md
│   └── references/
│       ├── allocation-and-reuse.md
│       ├── data-layout.md
│       └── benchmark-discipline.md
├── rust-unsafe-and-ffi/
│   ├── SKILL.md
│   └── references/
│       ├── safety-comment-template.md
│       ├── ffi-boundaries.md
│       └── maybeuninit-and-nonnull.md
├── arch-crate-design/
│   └── SKILL.md
├── domain-web-services/
│   └── SKILL.md
├── domain-cli-and-daemons/
│   └── SKILL.md
└── domain-embedded-and-iot/
    └── SKILL.md
```

This tree deliberately drops first-class skills for fintech, cloud-native, and
ML in the first pass. They are too specialised for the default Rust catalogue.
If later evidence shows repeated need, they can return as slim add-on skills or
domain-specific references.

## What each new skill should contain

Every first-class skill should use the same compact shape:

1. Trigger and scope in one short paragraph.

   State when to load it, when not to load it, and what question it is meant
   to answer.

2. Working stance in four to six bullets.

   This is the mindset framing, but compressed. It should feel like a calm,
   practical staff engineer setting direction, not a motivational speaker.

3. Decision surface.

   Give a short table or bullet list for the high-value forks. Examples:
   "borrow vs own vs clone", "generic vs `dyn`", "enum error vs erased error",
   "channel vs mutex vs actor", or "safe wrapper vs `unsafe fn`".

4. Red flags and escalation points.

   Name the traps that should cause redesign instead of local patching.

5. Pointer to references.

   Longer examples, comparisons, and edge-case notes go into `references/`.

## Compression rules for the rewrite

1. Remove generic explanations of Rust terms unless the explanation changes a
   decision the model would otherwise get wrong.

2. Replace repeated scaffolding with one consistent structure. The router may
   explain the catalogue shape once; the language skills should not keep
   re-teaching it.

3. Prefer one hard sentence over a full paragraph. Example style:
   "If a borrow error disappears after adding clones, re-check ownership design
   before keeping the clones."

4. Keep code examples short and only when prose is worse. Most should fit in
   six to twelve lines.

5. Remove ornamental formatting, novelty ASCII art, and protocol theatre.

6. Remove pseudo-mandatory workflows such as negotiation rituals unless they
   clearly improve Rust reasoning on real tasks.

## Domain and architecture posture

The new domain or architecture skills should not repeat the language mechanics.
Each one should do only three things:

1. Name the Rust-specific constraints that shape the architecture.
2. Point to the language skills most likely to matter.
3. Give the few patterns that are truly domain-specific.

`arch-crate-design` should cover crate boundaries, public versus internal APIs,
feature flags, error surface stability, and testability. The domain skills
should cover only domains where Rust materially changes the design surface in a
reusable way.

## Implementation milestones

1. Create `skills/` and add the new router plus one exemplar language skill.

   Start with `rust-router/` and `rust-memory-and-state/`. This proves the new
   structure, tone, and size budget before porting the rest.

2. Build the remaining language skills.

   Extract only the content that still earns its keep. Put every long
   comparison, tutorial, or example into `references/`.

3. Build the domain and architecture skills.

   Use the same compact structure. Each one should fit comfortably in the same
   size budget as a language skill.

4. Mark the old catalogue as superseded.

   Leave `current-skills/` intact until the new tree is complete, then add a
   short deprecation note or remove it in one deliberate follow-up change.

5. Validate discoverability and overlap.

   Read each new description and confirm that it triggers for the right tasks
   without duplicating another skill's purpose.

## Validation

The implementation phase should prove both size reduction and usefulness.

Run these checks after the new tree exists:

```plaintext
git diff --stat
find skills -name SKILL.md -print0 | xargs -0 wc -c | sort -n
rg -n \
  "Layer 1|Layer 2|Layer 3|Trace Up|Trace Down|Thinking Prompt|Negotiation" \
  skills
rg -n "[一-龥]" skills
```

Acceptance criteria:

1. The new top-level tree contains exactly one router, five to seven language
   skills, and three to five domain or architecture skills.
2. No new `SKILL.md` contains the removed repeated scaffold or non-English
   trigger catalogues.
3. The total size of the new `SKILL.md` set is materially smaller than the
   current set and each individual file is small enough for routine loading.
4. The new descriptions are specific enough that a future agent could choose
   the correct skill without opening three others first.

## Progress

- [x] 2026-03-09 14:09 GMT: Confirmed branch name `reduced-skill-footprint`
  and repository shape.
- [x] 2026-03-09 14:10 GMT: Inventory of `current-skills/` collected.
- [x] 2026-03-09 14:12 GMT: Measured current file sizes and repetition
  patterns.
- [x] 2026-03-09 14:18 GMT: Drafted reduction strategy and target `skills/`
  tree.
- [x] 2026-03-09 14:26 GMT: Implementation approved by user.
- [x] 2026-03-09 14:33 GMT: Added the router and six language skills under
  `skills/`, each with compact references.
- [x] 2026-03-09 14:37 GMT: Added four domain or architecture skills.
- [x] 2026-03-09 14:38 GMT: Verified the final committed first-class tree is
  one router, six language skills, and four domain or architecture skills.
- [x] 2026-03-09 14:36 GMT: Added architecture and domain skills plus
  [docs/skill-catalogue-status.md](/data/leynos/Projects/rust-skill/docs/skill-catalogue-status.md)
  to mark `skills/` as canonical without committing `current-skills/`.
- [x] 2026-03-09 14:48 GMT: Expanded `arch-crate-design` with workspace,
  publishability, helper-crate, metadata, and `cargo-binstall` guidance.
- [x] 2026-03-09 14:50 GMT: Added a concrete workspace layout example to
  `arch-crate-design`.
- [x] 2026-03-09 15:03 GMT: Swept the legacy anti-pattern material and ported
  the retainable descriptions into the contextual skills instead of reviving a
  standalone anti-pattern skill.

## Surprises & Discoveries

- The repository currently tracks almost nothing besides the initial commit.
  `current-skills/` is presently untracked, so this work is effectively a
  redesign plan rather than a migration on top of established history.
- The language catalogue is not merely verbose; it repeats the same headings
  and routing theory across many files, which makes superficial trimming
  unlikely to help enough.
- Nearly 35 KB of the current footprint is spent on Rust-specific tool-wrapper
  skills that should probably be replaced by one short pointer to general code
  navigation skills.

## Decision Log

1. Keep a router, but shrink it drastically.

   The router is worth preserving because it frames how to approach Rust
   problems. It is not worth preserving as an 8 KB meta-protocol with
   negotiation rituals and repeated taxonomy.

2. Merge by decision surface, not by old numbering.

   The old `m01` to `m15` split looks systematic but does not map cleanly to
   how Rust work happens. The new grouping is based on the real decisions an
   engineer makes under load: memory/state, types/APIs, errors, async,
   performance, and unsafe.

3. Drop tool wrappers from the Rust catalogue.

   They are useful instructions, but they are not Rust language expertise and
   they consume too much of the "Rust skill" footprint.

4. Prefer compact first-class skills plus references over giant default loads.

   This follows the user's stated goal and keeps the context window available
   for the actual task.

5. Do not commit `current-skills/`.

   The user explicitly asked to leave the source tree uncommitted. Treat it as
   local source material only; commit the new `skills/` tree and supporting
   docs without staging `current-skills/`.

6. `arch-crate-design` should cover packaging posture, not just layering.

   The useful version of this skill needs concrete guidance on when a workspace
   is justified, how inherited metadata and publish order affect design, how
   helper crates avoid cycles, when to ask for package metadata, and how to
   think about `cargo-binstall` support for binary crates.

7. Keep anti-pattern guidance contextual.

   The old `m15-anti-pattern` split is not worth preserving as a first-class
   skill. The worthwhile parts are local warnings attached to the relevant
   design pressure: clone-to-escape in ownership work, stringly APIs in type
   design, silent error swallowing in error handling, lock-across-await in
   async work, and premature collection or formatting churn in performance
   work.

## Outcomes & Retrospective

This draft establishes a concrete reduction target, a classification of what
should be deleted or merged, and a replacement `skills/` tree that fits the
requested shape. The next step is user approval. After approval, implementation
should proceed by creating the new router and one exemplar skill first, then
expanding the rest while holding the line on size and repetition.

Implementation reached the planned end state on 2026-03-09. The branch now has
one router, six language skills, four domain or architecture skills, compact
references for the language set, and an explicit note that `current-skills/`
is legacy source material rather than committed output.

Validation passed with `markdownlint-cli2 docs/**/*.md 'skills/**/*.md'` and
`git diff --check`. The final first-class `SKILL.md` footprint is 18,279 bytes,
down from the 194,029-byte `current-skills/` baseline.
