---
name: verus
description: Write and maintain Verus deductive proofs for Rust code. Use for formal verification of pure functions, ordering invariants, mapping logic, and properties that require unbounded reasoning beyond bounded model checking, and for wiring Verus into a repository through rust-prover-tools.
---

# Verus deductive verification for Rust

Verus uses the Z3 SMT solver to statically verify that executable Rust
code satisfies user-provided specifications, with zero runtime cost. Load
the `rust-verification` skill first for the selection rules; load this
skill once Verus is the chosen tool.

## When to apply

Apply when:

- a property holds over unbounded domains (arbitrary-length sequences,
  any number of layers, all possible orderings),
- a pure function must satisfy algebraic properties (reflexivity,
  antisymmetry, transitivity, totality),
- extraction or transformation logic that must preserve structure needs
  verification,
- a Kani harness keeps growing because the bounded state space is too
  large — extract the pure helper and prove it in Verus instead.

Do not apply when bounded symbolic execution (Kani) would suffice, the
code is dominated by I/O or concurrency, a property test would give
enough confidence, or the code uses features Verus does not support
(`async`, most `unsafe`, raw concurrency). Verus arrives last in a
repository's verification stack: "only after there is something small
and stable enough to prove". Proofs that depend on collection internals
or bit-level mixing become expensive quickly; pick semantic seams.

## Installation and runs

Use [`rust-prover-tools`](https://github.com/leynos/rust-prover-tools) as
the canonical installer and runner. The tool handles version pinning,
checksum verification, toolchain installation, and proof execution
through a single CLI:

```bash
# Install the pinned Verus release for this target.
prover-tools verus install --repo-root .

# Run Verus against a proof file (preserves Verus's exit code).
prover-tools verus run --repo-root . --proof-file verus/my_proofs.rs
```

`install` reads the pinned version and checksum from in-tree files
(defaults: `tools/verus/VERSION` and `tools/verus/SHA256SUMS`; overridden
with `--version-file` and `--checksum-file`). `run` resolves the binary
(from `--verus-bin`, the install directory, or `PATH`), ensures the
required Rust toolchain is installed via `rustup`, and executes the
proof. Repeatable `--extra-arg` is appended after the proof file. Do not
reintroduce shell wrappers; every retired script drew review findings
(missing checksums, swallowed exit codes, flag passthrough breakage).
See [`references/installation-note.md`](references/installation-note.md)
for the rationale and
[`references/project-on-ramp.md`](references/project-on-ramp.md) for the
pin files, Makefile targets, layout, and contract tests reviewers expect.

## Core concepts

Three modes coexist:

| Mode    | Purpose                   | Compiled?  |
| ------- | ------------------------- | ---------- |
| `spec`  | Mathematical descriptions | no (ghost) |
| `proof` | Establish facts           | no (ghost) |
| `exec`  | Ordinary Rust             | yes        |

Ghost code (`spec` and `proof`) is erased; it has no runtime cost.

All Verus-verified code lives inside `verus! { ... }`:

```rust
use vstd::prelude::*;

verus! {

pub type ItemId = nat;

pub open spec fn is_in_range(id: ItemId) -> bool { id < 1000 }

proof fn lemma_in_range_is_bounded(id: ItemId)
    requires is_in_range(id),
    ensures id < 1000,
{ /* trivial by definition */ }

} // verus!
```

`requires` and `ensures` form the contract between functions; callers
satisfy `requires`, callees rely on `ensures`. Recursive `spec fn` and
`proof fn` need a `decreases` clause.

`open spec fn` exposes the body to callers; `closed spec fn` hides it
and forces callers to use the `ensures` clause. Most spec functions
should be `open`.

## Writing a good proof

A proof is modular, trigger-aware, and context-disciplined. Compose
small lemmas; scope auxiliary proofs aggressively.

### Composing sub-lemmas

```rust
proof fn lemma_edge_leq_total_ordering()
    ensures total_ordering(|a: EdgeSpec, b: EdgeSpec| edge_leq(a, b)),
{
    reveal(total_ordering);
    lemma_edge_leq_reflexive();
    lemma_edge_leq_antisymmetric();
    lemma_edge_leq_transitive();
    lemma_edge_leq_strongly_connected();
}
```

Each property has its own small lemma. The top-level lemma composes them
after `reveal`ing the opaque `total_ordering` definition. A lemma that
ensures a compound property by asserting that same property in one bare
`assert` will not verify and reads as an admitted claim; reviewers ask
for exactly this decomposition.

### Inductive proofs over sequences

```rust
proof fn lemma_extract_from_sequence_invariants(items: Seq<ItemSpec>)
    ensures extract_invariants(items),
    decreases items.len(),
{
    if items.len() == 0 {
        // Base case: Z3 discharges automatically.
    } else {
        let rest = items.drop_first();
        lemma_extract_from_sequence_invariants(rest);
        // Plus a glue lemma that prepend or concat preserves invariants.
    }
}
```

For a longer worked composition (canonicalisation, total-ordering, and
the inductive extraction skeleton), see
[`references/proof-examples.md`](references/proof-examples.md) and
[`references/verus-proof-example.rs`](references/verus-proof-example.rs).

### Anti-patterns

- **Unscoped helper lemmas** pollute the proof context with universal
  quantifiers, burdening Z3 on every subsequent goal. Use
  `assert(F) by { lemma_helper(...) }` to contain them.
- **Missing or auto-mismatched triggers** cause "obvious" proofs to
  fail. See the trigger section below.
- **`assume` left in a proof** is a soundness hole. A stray
  `assume(false)` proves anything. Use `assume` only as a temporary
  placeholder; eliminate it before declaring the proof complete.
- **A lemma that restates its definition.** `spec_p(x) <==>
  definition_of(spec_p)` proves nothing; assert something beyond the
  spec function's own body.
- **Axioms that stop at the leaf.** A trust-boundary axiom used by a
  helper lemma must appear in the `requires` of every wrapper lemma.
- **Speculative generics.** Specialize scaffolding to the concrete type
  actually verified.

## Triggers

Triggers control how Z3 instantiates universal quantifiers. A trigger
must contain all bound variables and may not contain equality,
arithmetic, or boolean operators (function calls, indexing, and field
access are valid).

```rust
// Explicit:
forall|i: int| 0 <= i < s.len() ==> #[trigger] is_valid(s[i])

// Auto (Verus selects and prints a note):
forall|i: int| #![auto] 0 <= i < s.len() ==> is_valid(s[i])

// Multiple triggers:
forall|i: int, j: int|
    #![trigger a[i], b[j]]
    #![trigger a[i], c[j]]
    0 <= i < j < a.len() ==> a[i] != b[j] && a[i] != c[j]
```

### The trigger trap

If `requires forall|i: int| 0 <= i < s.len() ==> #[trigger] is_even(s[i])`,
then `assert(s[3] % 2 == 0)` fails because `is_even` never appears in
the assertion. Assert the trigger-matching expression first:

```rust
assert(is_even(s[3]));    // Instantiates for i = 3.
assert(s[3] % 2 == 0);   // Now uses the fact above.
```

### Matching loops

A matching loop instantiates a trigger and produces a new expression that
matches the same trigger again, growing without bound. The classic shape
`#[trigger] s[i] <= s[i + 1]` is unsafe: matching `i = 2` produces
`s[3]`, which matches `i = 3` producing `s[4]`, and so on. Prefer two
already-present indices:

```rust
forall|i: int, j: int|
    #![trigger s[i], s[j]]
    0 <= i <= j < s.len() ==> s[i] <= s[j]
```

Workflow: start with `#![auto]`, review the auto-trigger note Verus
prints, check the concrete assertions against the trigger, and add
explicit `#[trigger]` annotations when the match fails or loops. Do not
ignore trigger warnings; treat each one as a review item.

## `assert(F) by { ... }`

When establishing `F` requires an auxiliary lemma, scope that lemma's
quantifiers to the inner block:

```rust
proof fn example(s: Seq<int>) {
    assert(some_fact(s)) by { lemma_about_sequences(s); };
    // Only some_fact(s) is in scope here; lemma's quantifiers are not.
    assert(another_fact(s));
}
```

This is one of the most important patterns for keeping proofs fast.

## Nonlinear arithmetic

Z3 handles linear arithmetic well; nonlinear (`x * y` where neither is
constant) is off by default. Three options:

- `assert(...) by(nonlinear_arith) requires ...` — general-purpose but
  unpredictable.
- `proof fn lemma(...) by(integer_ring)` — decidable for equational ring
  theory; `int` only, no inequalities, no division.
- Fall back to manual lemmas from `vstd::arithmetic`.

A common pattern: prove identities with `integer_ring`, then close the
inequality with `nonlinear_arith` over the identity.

## Project layout and the production bridge

Keep Verus proof files in a dedicated directory at the repository root,
separate from the Cargo workspace:

```text
project/
├── Cargo.toml
├── src/
├── verus/
│   ├── my_proofs.rs          # types, specs, top-level lemmas
│   ├── my_proofs_extract.rs  # extraction invariant proofs
│   └── my_proofs_ordering.rs # ordering proofs
└── tools/
    └── verus/
        ├── VERSION
        └── SHA256SUMS
```

Sub-files use `mod` declarations from the root and `use super::*` to
share spec types and definitions. Run via `prover-tools verus run
--proof-file verus/my_proofs.rs`.

Verus is not a Cargo dependency: it compiles its own files. Production
crate modules cannot be `use`d directly. Two bridges exist and both
decay unless maintained:

- **Spec mirror.** Mirror production structs as `spec` structs and keep
  them in sync by code review. Document, on each spec item, which
  runtime type and function it models; spec items are public API.
- **`#[path]` import.** Pull the production type in directly, and add a
  CI check that the path and the referenced type still exist, because
  Verus will not notice a rename until the proof is next run.

A proof over an idealized structure (`Seq<nat>`) says nothing about a
differently shaped runtime structure (`BTreeMap`) until an explicit
refinement lemma connects them. Reviewers look for that bridge; "the
lemmas here do not justify the shipped implementation" is the finding
when it is absent.

## Project integration

- Keep `make verus` out of `make test`, `make lint`, `make all`, and
  the pull-request gate until the proofs have been stable; run it on a
  schedule or on demand. Until real proofs exist, ship the target as an
  explicit `FORMAL-SKIP` stub rather than a silently green one.
- `#[allow]` is forbidden in `verus/` exactly as in production; use
  `#[expect(dead_code, reason = "...")]` on the specific spec-only item.
  Every file starts with `//!`; every `pub(super) proof fn` carries
  `///`.
- Record in the developers' guide which properties each proof file
  covers and which it does not, and keep ExecPlan `Status:` and ADR
  text in agreement with the proofs.
- The full pre-submission checklist is in
  [`references/review-failure-modes.md`](references/review-failure-modes.md).

## Hard-won lessons

- **Triggers are not optional.** When a logically obvious proof fails,
  check the trigger before the logic.
- **`assert` in Verus is not `assert!` in Rust.** Inside `verus! { }`,
  `assert` is a verification request; outside, `assert!` is a runtime
  panic.
- **`broadcast use vstd::seq::group_seq_axioms;`** is required for
  proofs that manipulate sequences with `add`, `push`, or indexing
  across concatenations. Without it, proofs fail mysteriously.
- **Proof context pollution causes timeouts.** Wrap helper lemma calls
  in `assert(...) by { ... }`.
- **The Z3 timeout cliff is nonlinear.** One extra `forall` can push a
  half-second proof past the timeout. Split into smaller lemmas before
  raising the timeout.
- **Index arithmetic in quantifiers** (`i - 1`, `i + 1`) defeats trigger
  matching. Bind an auxiliary variable and assert its bounds first.
- **`reveal(name)`** is required before reasoning about opaque `vstd`
  definitions such as `total_ordering`.
- **The mirror is part of the proof.** A spec struct or `#[path]` import
  that has drifted from production makes every lemma downstream a
  statement about nothing.

## References

- [Verus Guide](https://verus-lang.github.io/verus/guide/),
  [GitHub](https://github.com/verus-lang/verus),
  [releases](https://github.com/verus-lang/verus/releases),
  [vstd docs](https://verus-lang.github.io/verus/verusdoc/vstd/),
  [playground](https://play.verus-lang.org/).
- [`references/project-on-ramp.md`](references/project-on-ramp.md) for
  pins, Makefile targets, layout, the production bridge, and contract
  tests.
- [`references/review-failure-modes.md`](references/review-failure-modes.md)
  for the pre-submission checklist drawn from estate review history.
- [`references/proof-examples.md`](references/proof-examples.md) for a
  canonicalisation proof, an inductive concat lemma, and a total-ordering
  composition.
- [`references/verus-proof-example.rs`](references/verus-proof-example.rs)
  for a self-contained Rust source illustrating the project layout, spec
  structs, and lemma composition.
- The survey behind this guidance:
  `docs/verification-review-failure-modes.md` in the catalogue repository.
