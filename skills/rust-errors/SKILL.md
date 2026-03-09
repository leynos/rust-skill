---
name: rust-errors
description: Use for Rust error design, `Result` shape, panic boundaries, context propagation, library vs binary handling, retryability, and failure classification.
globs: ["**/Cargo.toml", "**/*.rs"]
---

# Rust Errors

Use this when the problem is not "how do I return an error" but "what failure
shape belongs at this boundary?"

## Working stance

- Keep library errors typed and inspectable.
- Let binaries optimise for reporting and context.
- Panic only for broken invariants, not expected failure.
- Add context where it helps a future reader act.
- Separate retryable, terminal, and caller-bug failures early.

## Decision surface

| Boundary | Default move |
| --- | --- |
| library or reusable crate | typed error enum |
| binary, tool, integration glue | `anyhow`-style reporting is fine |
| expected invalid input | `Result` |
| impossible state if invariants hold | panic or debug assertion with care |
| need source preservation | wrap and chain |
| retry policy depends on cause | classify explicitly, do not parse strings |

## Red flags

- `.unwrap()` is used in production paths,
- error messages become the contract because types are too vague,
- caller mistakes, transient IO, and invariant breaks share one bucket,
- context is added everywhere but none of it helps triage,
- a public API returns `Box<dyn Error>` because design ran out of time.

Read [library-vs-binary-errors.md](references/library-vs-binary-errors.md) and
[retry-cancel-classification.md](references/retry-cancel-classification.md) if
the boundary or policy is still fuzzy.
