# Verus review failure modes

Findings on Verus proofs are few (28 across the estate, from four
repositories) because few repositories have shipped proofs. Almost half
concern install scripts that `prover-tools` now replaces. The rest are
below, with the rule each teaches.

## Proof structure

- **A compound `ensures` backed by one bare `assert`.** A lemma that
  ensures `total_ordering(..)` by asserting `total_ordering(..)` "appears
  to rely on an unproved `assert`, so the Verus proof likely won't
  verify". Split into one helper lemma per sub-property (reflexive,
  antisymmetric, transitive, strongly connected) and compose them after
  `reveal`.
- **A lemma that restates a definition.** `spec_p(x) <==>
  definition_of(spec_p)` proves nothing; a lemma must assert something
  beyond the spec function's own body.
- **Axioms not propagated.** When a helper lemma depends on a
  trust-boundary axiom, every wrapper lemma's `requires` must carry it,
  not only the leaf.
- **Speculative generics.** Specialize spec functions, axiom blocks, and
  lemmas to the concrete type verified; generic scaffolding is
  maintenance surface with no proof value.
- **Trigger warnings.** "Do not ignore Verus trigger warnings." Treat
  the auto-trigger note as a review item, and fix matching loops before
  raising `--rlimit`.

## Spec-mirror drift and refinement

- **Idealized structures.** "A Verus proof over an idealised data
  structure (e.g. `Seq<nat>`) does not, by itself, prove anything about
  a differently-shaped runtime structure (e.g. a sparse `BTreeMap`)
  unless an explicit abstraction/refinement lemma bridges the two."
  The reviewer's verdict on the offending PR: "the lemmas here do not
  justify the shipped implementation". Deferred to an issue.
- **`#[path]` imports without an existence check.** Verus does not link
  against production, so a renamed type breaks nothing until the proof
  is next run. Add a CI check that the path and type still exist.
- **Undocumented spec items.** Spec functions are public API; document
  each one's relationship to the runtime model it describes, not only
  its logical statement.

## Gating and claims

- Verus stays out of `make test`, `make lint`, `make all`, and the
  pull-request formal gate until proofs are stable; it "should arrive
  only after there is something small and stable enough to prove".
- An ADR that rejects Verus (or proptest, or Kani) is read critically:
  `lille` #285 had its rejection overruled because `i64` weights and
  path strings are not finite domains, and then had to stop claiming
  that the amendment "closes" the gap.
- ExecPlan `Status:` fields and gating language must agree with each
  other and with the code.
- A proof file's coverage claim must match its lemmas; a caption that
  overstates what is proved is a review defect.

## Lint policy in `verus/`

- `#[allow]` forbidden; `#[expect(dead_code, reason = "...")]` on the
  specific spec-only item, never `#![allow(dead_code)]` on the module.
- Rustdoc `///` required on every `pub(super) proof fn`.
- Module-level `//!` comment required.
- Oxford spelling everywhere, including tool READMEs.

## Toolchain and install (now handled by `prover-tools`)

Recorded so the reasons for the mandatory route are not lost:

- release archives fetched without checksum verification;
- exit status captured after a negated `!` compound, so the gate could
  never fail;
- runner iterating several proof files and propagating only the last
  exit status;
- multiple `trap` handlers on one signal silently overwriting each
  other;
- flags mistaken for positional file arguments, breaking `--version`
  passthrough;
- sibling scripts resolved from the caller's cwd instead of
  `${BASH_SOURCE[0]}`;
- `rustup install` instead of `rustup toolchain install`; toolchain
  identifiers with channel and date suffixes parsed as plain semver;
- Bash 3.2 (macOS) incompatibilities: unquoted command-substitution
  arrays, `mapfile`, process substitution;
- inside `prover-tools` itself: the install fallback dropped the
  caller's `--target`; `rustup` was demanded before the version probe
  had failed; relative `--repo-root` overrides were not resolved
  against the root.
