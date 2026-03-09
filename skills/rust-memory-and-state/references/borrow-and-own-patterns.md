# Borrow and Own Patterns

Use these defaults:

- Function takes data but does not keep it: `&T`, `&str`, `&[T]`, or `&mut T`.
- Function stores or returns data beyond the caller's scope: own it.
- Struct with hard lifetimes and unclear invariants: prefer owned fields before
  adding more parameters.
- Expensive clone introduced to satisfy one branch: ask whether the branch
  should consume the value instead.

Short example:

```rust
fn parse_name(input: &str) -> Result<Name, ParseError> {
    Name::parse(input)
}

struct User {
    name: Name,
}
```

`Cow` is worth considering only when a hot path genuinely alternates between
borrowed and owned data.
