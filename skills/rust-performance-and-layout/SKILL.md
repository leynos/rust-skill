---
name: rust-performance-and-layout
description: Use for Rust performance work, allocation pressure, data layout, hot-path APIs, benchmarks, and when layout or copying choices affect runtime behaviour.
globs: ["**/Cargo.toml", "**/*.rs"]
---

# Rust Performance and Layout

Use this when performance matters enough to justify design pressure.

## Working stance

- Measure before changing shapes.
- Fix the largest hot-path cost, not the most obvious micro-optimization.
- Reuse allocations and tighten data movement before reaching for cleverness.
- Keep layout decisions explicit when they affect cache use or FFI.
- Prefer simple code unless profiling proves it is the bottleneck.

## Decision surface

| Pressure | First move |
| --- | --- |
| repeated allocation | reuse buffers, pre-size collections |
| large enum or struct footprint | inspect layout, box rare large fields |
| string and byte churn | borrow or use slices/bytes where lifetimes allow |
| clone-heavy hot path | revisit ownership and API boundaries |
| "faster" rewrite with no numbers | benchmark first |

## Red flags

- benchmarking starts after the rewrite,
- tiny local wins complicate the API surface,
- hot-path code formats strings or allocates collections repeatedly,
- data layout changes happen without measuring access patterns,
- unsafe code is introduced before safe structural fixes are tried.

Read [allocation-and-reuse.md](references/allocation-and-reuse.md),
[data-layout.md](references/data-layout.md), and
[benchmark-discipline.md](references/benchmark-discipline.md) for the common
forks.
