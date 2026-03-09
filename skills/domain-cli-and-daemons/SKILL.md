---
name: domain-cli-and-daemons
description: Use for Rust CLIs, workers, daemons, batch jobs, and services where process lifecycle, operator feedback, and shutdown rules matter.
globs: ["**/Cargo.toml", "**/*.rs"]
---

# Rust CLI and Daemon Work

Use this when the program is a process boundary first: command-line tool,
worker, daemon, long-running job, or supervisor-managed service.

## Working stance

- Keep parsing, config loading, and reporting at the edge.
- Make process lifetime explicit: startup, steady state, shutdown, exit code.
- Write machine-readable output to stdout and diagnostics to stderr.
- Long-running jobs need supervision, cancellation, and cleanup contracts.
- Pair this skill with `rust-errors`; add `rust-async-and-concurrency` only if
  lifecycle or parallelism is the real pressure.

## Domain pressure

- Config precedence should be stable and unsurprising.
- Exit codes are part of the interface.
- Background workers must decide who owns retries, backoff, and shutdown.
- Progress reporting should never corrupt data output.

## Red flags

- `main` contains business logic and retry loops,
- shutdown depends on ad hoc signal handling spread across modules,
- human output and machine output share the same channel,
- daemon state is shared globally because ownership was never assigned.
