# Y-Statement template and Rust examples

The Y-Statement format compresses a decision into six clauses:

```text
In the context of <use case>,
facing <concern>,
we decided for <option>,
and against <alternatives>,
to achieve <quality>,
accepting <downside>.
```

Each clause is one sentence. The record is one file under `docs/adr/`.

## File template

```markdown
# ADR-NNNN: <short title>

- Status: Accepted | Proposed | Superseded by ADR-MMMM
- Date: YYYY-MM-DD
- Deciders: <names or team>

## Context and decision

In the context of <use case>,
facing <concern>,
we decided for <option>,
and against <alternatives>,
to achieve <quality>,
accepting <downside>.

## Consequences

- <observable change for callers, contributors, or operators>
- <observable change>
- <observable change>
```

## Example 1: typestate for a request builder

```markdown
# ADR-0002: Typestate for `RequestBuilder`

- Status: Accepted
- Date: 2026-04-12
- Deciders: API working group

## Context and decision

In the context of the public `RequestBuilder` for our HTTP client,
facing the long-running complaint that `build()` panics when required
fields are missing,
we decided for a typestate machine (`Empty → WithUrl → WithBody`) that
exposes `build()` only on the terminal state,
and against runtime validation, a `Result<Request, Error>` return type,
or a separate `RequestBuilderUnchecked`,
to achieve compile-time enforcement of the required-field contract
without a fallible terminal call,
accepting that intermediate states are visible in the public API and
that recursive macros over the builder become harder to write.

## Consequences

- The public API gains three marker types; documentation lists them
  in the `Empty` introduction.
- The 0.x → 1.0 SemVer bump is required: existing callers that
  destructure or store a `RequestBuilder` change types.
- Error handling around `build()` collapses to the type system; the
  custom `BuildError` enum is removed.
```

## Example 2: choosing a verification tool

```markdown
# ADR-0003: Use Verus for the edge-ordering proof

- Status: Accepted
- Date: 2026-05-03
- Deciders: Graph team

## Context and decision

In the context of the `EdgeSet::sort_by` ordering invariant,
facing a Kani harness that timed out at four nodes and was projected
to scale combinatorially,
we decided for a Verus deductive proof of total ordering over an
unbounded sequence,
and against extending the Kani unwind bound, switching to a property
test, or accepting the limit,
to achieve a proof that holds for sequences of arbitrary length,
accepting that the production `EdgeSpec` struct must be mirrored as a
Verus `spec` struct and kept in sync by review.

## Consequences

- `verus/edge_ordering_proofs.rs` joins the repository; CI runs it via
  `prover-tools verus run`.
- The Kani harness for ordering is removed; the harness for structural
  bidirectionality stays.
- Reviewers of `EdgeSpec` must update the Verus mirror in the same PR.
```

## Example 3: choosing an `unsafe` invariant

```markdown
# ADR-0004: `BorrowedSlice` permits non-aligned `T`

- Status: Accepted
- Date: 2026-05-19
- Deciders: Unsafe review group

## Context and decision

In the context of the `BorrowedSlice<T>` FFI shim,
facing pressure from callers passing pointers from C structs without
alignment guarantees,
we decided for a documented invariant that the pointer is valid for
reads but not necessarily aligned for `T`, with all reads performed
via `read_unaligned`,
and against requiring caller-provided alignment, copying into an
aligned buffer, or panicking on misalignment,
to achieve a zero-copy bridge that matches the C calling convention,
accepting a small per-element cost on architectures where unaligned
loads are emulated.

## Consequences

- The `# Safety` section on `BorrowedSlice::new` is rewritten to drop
  the alignment requirement.
- Miri tests gain a misaligned-pointer harness.
- `read_unaligned` becomes a project convention for FFI slice
  accessors; ADR-0007 generalizes it to `BorrowedMutSlice`.
```

## Practical rules

- The "against" clause must name real alternatives that were
  considered and rejected, not strawmen.
- The "accepting" clause must name a real downside; if none exists,
  the decision is probably not worth an ADR.
- Cross-reference related ADRs by number; keep the title short.
- When superseding, both files keep their original "Date" and
  "Deciders" lines; the new file's status mentions the superseded
  number and the old file's status flips to "Superseded by ADR-NNNN".

## Reading list

- The Y-Statement format is described in Olaf Zimmermann et al.,
  ["Sustainable architectural design decisions"](https://www.ifs.hsr.ch/fileadmin/user_upload/customers/ifs/Dokumente/projekte/Sustainable_Architectural_Design_Decisions.pdf).
- Michael Nygard's
  [original ADR essay](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
  introduces the broader practice; the Y-Statement is one of several
  templates that fit inside it.
