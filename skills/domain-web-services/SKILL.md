---
name: domain-web-services
description: Use for Rust HTTP services, request handlers, middleware, shared state, backpressure, and shutdown behaviour in web-facing systems.
globs: ["**/Cargo.toml", "**/*.rs"]
---

# Rust Web Services

Use this when request lifecycle, service state, and failure reporting shape the
Rust design.

## Working stance

- Keep handlers thin; move business rules behind service boundaries.
- Parse and validate at the edge, then hand typed data inward.
- Shared state should have a clear owner and a narrow mutation story.
- Timeouts, backpressure, and shutdown are part of correctness.
- Pair this skill with `rust-async-and-concurrency` or `rust-errors`, not both
  by default.

## Domain pressure

- Request state is short-lived, so borrowed data is often enough inside one
  request path.
- Shared caches, pools, and coordination state need explicit thread-safe
  ownership.
- Status-code mapping and retry policy should follow typed failure classes,
  not string inspection.
- Middleware should enforce cross-cutting rules without owning business logic.

## Red flags

- handlers own large chunks of domain logic,
- request code reaches into `Arc<Mutex<_>>` everywhere,
- blocking work sits on the async executor,
- transport-layer errors and domain failures collapse into one response path.
