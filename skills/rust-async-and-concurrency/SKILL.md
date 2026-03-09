---
name: rust-async-and-concurrency
description: Use for async Rust, task ownership, `Send` and `Sync`, shared state, channels, cancellation, blocking boundaries, runtimes, and shutdown behaviour.
globs: ["**/Cargo.toml", "**/*.rs"]
---

# Rust Async and Concurrency

Use this when work crosses task or thread boundaries, or when runtime and
shutdown behaviour shape the design more than syntax does.

## Working stance

- Decide who owns a task and how it stops before wiring the happy path.
- Prefer message passing over shared mutable state when ownership is unclear.
- Keep blocking and CPU-heavy work out of async executors.
- Treat `Send` and `Sync` errors as design feedback, not compiler trivia.
- Cancellation needs an explicit contract, not just dropped futures.

## Decision surface

- One owner processes updates: use a channel or actor loop.
- Shared mutable state is small and unavoidable: use a lock with tight scope.
- Async code must call blocking or CPU-heavy work: use `spawn_blocking` or a
  dedicated thread.
- Graceful shutdown matters: define a cancellation signal and join path.
- Fire-and-forget looks tempting: prefer an owned task handle instead.
- Data must cross threads in async code: use owned captures and `Send` types.

## Red flags

- `Arc<Mutex<_>>` spreads through handlers and tasks,
- spawned tasks outlive the code that should supervise them,
- cancellation means "drop it and hope",
- blocking DB, filesystem, or compression work runs on the async executor,
- `!Send` state leaks into multithreaded runtime code by accident.

Read [send-sync-checklist.md](references/send-sync-checklist.md),
[task-ownership.md](references/task-ownership.md), and
[blocking-and-backpressure.md](references/blocking-and-backpressure.md) when
the runtime contract is the hard part.
