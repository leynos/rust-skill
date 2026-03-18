---
name: rust-memory-and-state
description: Use for ownership, borrowing, lifetimes, aliasing, smart pointers, interior mutability, resource acquisition is initialisation (RAII), and resource handoff in Rust.
globs: ["**/Cargo.toml", "**/*.rs"]
---

# Rust Memory and State

Use this when the question is really "who owns this, who may mutate it, and
how long must it stay valid?"

## Working stance

- Prefer one clear owner and cheap borrowed reads.
- Reach for cloning last, not first.
- If cloning appears mainly to placate the borrow checker, fix the data flow
  before keeping the clone.
- Treat `Rc`, `Arc`, `RefCell`, `Mutex`, and `RwLock` as ownership decisions,
  not syntax bandages.
- If a lifetime gets hard to express, ask whether the type should own the data.
- Use RAII to make cleanup happen by scope, not by hope.

## Decision surface

| Need | Default move |
| --- | --- |
| read-only, caller keeps ownership | borrow `&T` or `&mut T` |
| return data past the borrower's scope | own it |
| cheap duplicated scalar/value type | `Copy` or explicit clone |
| shared single-thread ownership | `Rc<T>` |
| shared cross-thread ownership | `Arc<T>` |
| mutation behind shared access, single-thread | `RefCell<T>` |
| mutation behind shared access, multi-thread | `Mutex<T>` or `RwLock<T>` |
| resource cleanup tied to scope | RAII guard or owning wrapper |

## Red flags

- clones multiply each time the borrow checker complains,
- `Rc` or `Arc` shows up where one owner plus borrowed readers would do,
- `Arc<Mutex<T>>` appears before the real sharing pattern is known,
- references are stored where owning data would simplify the type,
- resource release depends on "remember to call close()",
- `'static` is used to silence a lifetime problem instead of explaining one.

Read [borrow-and-own-patterns.md](references/borrow-and-own-patterns.md) for
API choices, [interior-mutability.md](references/interior-mutability.md) for
shared mutation, and [lifecycle-and-raii.md](references/lifecycle-and-raii.md)
for resource scope patterns.
