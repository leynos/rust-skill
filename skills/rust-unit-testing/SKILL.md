---
name: rust-unit-testing
description: Design and maintain Rust unit tests with clear helper boundaries, rstest fixtures and parameterization, serial_test isolation, fallible setup, and rich assertions with googletest, pretty_assertions, and insta. Use when refactoring assertion helpers, replacing brittle boolean assertions, shaping table tests, or deciding between equality, matcher, and snapshot assertions.
---

# Rust unit testing

Use this when the problem is not "how do I run `cargo test`" but "how should
this Rust test be shaped so failures explain the defect?"

## Working stance

- Keep setup, query, and assertion as separate concerns.
- Prefer pure query helpers that return data over helpers that panic halfway
  through the inspection.
- Make fallible setup explicit with `Result` and unwrap only at the test
  boundary with useful context.
- Use table tests for behaviour matrices, not for unrelated stories forced
  into one function.
- Serialize only tests that touch global state; otherwise let Cargo run them
  in parallel.
- Pick the assertion tool that makes the failing value easiest to inspect.

## Test shape

- Repeated setup object: `#[fixture]` from `rstest`.
- Behaviour matrix: `#[rstest]` plus named `#[case]` inputs.
- Fallible setup: fixture or helper returns `Result<T, E>`; test returns
  `Result<()>` or calls `.expect("specific setup context")`.
- Global env, cwd, process state, singleton, or shared port: `#[serial]` from
  `serial_test`, preferably with a key.
- Simple scalar equality: `pretty_assertions::assert_eq!` in tests.
- Nested data, collections, variants, options, or text predicates:
  `googletest::assert_that!` with matchers.
- Large formatted output, diagnostics, generated code, command-line text, or
  structured JSON/YAML: `insta` snapshot.

## rstest fixtures and cases

Use `rstest` when the test body is stable and the inputs vary. Name each case
after the behaviour it proves, because those names become the first debugging
surface in failing output.

```rust
use rstest::{fixture, rstest};

#[fixture]
fn parser() -> Parser {
    Parser::default()
}

#[rstest]
#[case::trims_outer_whitespace("  alpha  ", "alpha")]
#[case::preserves_inner_whitespace("alpha  beta", "alpha  beta")]
fn parses_names(parser: Parser, #[case] input: &str, #[case] expected: &str) {
    assert_eq!(parser.parse_name(input).unwrap(), expected);
}
```

Keep fixture graphs shallow. If a fixture has several inputs and side effects,
split it into a builder helper plus a fixture that chooses the common default.
For fallible fixtures, return the fallible value and let the test decide
whether to use `?`, `expect`, or assert on the error.

## serial_test

Use `serial_test` for tests that cannot safely run concurrently because they
mutate process-wide state: environment variables, current directory, global
loggers, static registries, fixed network ports, or shared external resources.
Give related tests the same key so they serialize with each other without
blocking unrelated serial groups.

```rust
use serial_test::serial;

#[test]
#[serial(current_dir)]
fn reads_config_from_current_directory() {
    let temp = tempfile::tempdir().unwrap();
    let _cwd = CurrentDirGuard::push(temp.path()).unwrap();

    assert!(load_config().is_ok());
}
```

`CurrentDirGuard` should be a small test helper that restores the previous
directory in `Drop`.

Do not add `#[serial]` to hide order dependence. If the test can own its temp
directory, port, clock, or configuration, isolate that dependency instead.
Reach for file-lock variants only when separate test processes must coordinate
against the same external resource.

## Assertion choice

Use `pretty_assertions` as the low-cost default when `assert_eq!` already says
the right thing but the diff is hard to read:

```rust
use pretty_assertions::assert_eq;
```

Use `googletest` when the shape matters more than raw equality or when a
boolean assertion would erase the reason for failure:

```rust
use googletest::prelude::*;

assert_that!(
    rendered_error,
    contains_substring("source should be a supported error source"),
);
```

Use `insta` when the expected value is a substantial artefact. Snapshot the
stable output of a pure renderer or formatter, use redactions for volatile
fields, and review snapshot updates deliberately. Inline snapshots are useful
for small strings; checked-in `.snap` files are better for larger output.

```rust
insta::assert_json_snapshot!(rendered_error, {
    ".timestamp" => "[timestamp]",
});
```

## Helper design

Test helpers should have one job. A helper that downcasts, normalizes,
compares, and panics is doing too much: failures become vague, and the
interesting logic cannot be tested independently.

Split helpers into:

- a fallible extractor that returns a typed actual value,
- a pure query or predicate that can be asserted directly,
- a thin assertion wrapper that exists only to improve failure output.

Read
[`references/helper-refactor-example.md`](references/helper-refactor-example.md)
for the worked dynamic-error-source example.

## Red flags

- A helper name starts with `assert_` but performs setup or discovery.
- A test fixture reaches into env vars, cwd, global state, or the filesystem
  without owning the reset path.
- `#[serial]` appears on a whole module because one test was flaky.
- A `matches!` assertion has a long custom message and still hides the actual
  value.
- Snapshots include timestamps, IDs, absolute paths, random ordering, or host
  paths without redaction or sorting.
- A table test has ten columns and only two rows; a named scenario test would
  be clearer.

## References

- [`rstest`](https://docs.rs/rstest/latest/rstest/) for fixtures and
  parameterized cases.
- [`serial_test`](https://docs.rs/serial_test/latest/serial_test/) for
  serial groups and file-lock-backed variants.
- [`googletest`](https://docs.rs/googletest/latest/googletest/) for matcher
  assertions.
- [`pretty_assertions`](https://docs.rs/pretty_assertions/latest/pretty_assertions/)
  for diff-friendly equality assertions.
- [`insta`](https://docs.rs/insta/latest/insta/) and
  [Insta documentation](https://insta.rs/docs/) for snapshot testing.
