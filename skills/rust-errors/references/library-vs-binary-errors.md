# Library vs Binary Errors

Use typed errors in libraries because callers need structure.

Use application-level wrappers in binaries because the top-level job is
reporting, logging, and exit behaviour.

Good split:

- library crate: `thiserror` enum or equivalent,
- binary crate: add context at boundaries and report once near `main`.

If a library returns `anyhow::Error`, it usually means the error contract was
left underspecified.
