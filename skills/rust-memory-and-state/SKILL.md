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

## Polonius Alpha posture

When the router identifies `polonius-alpha`:

- try the direct conditional-borrow or reborrow form before adding clones,
  repeated lookups, borrow-dodging ids, or interior mutability;
- distinguish a lifetime that NLL over-extends from two borrows that are
  genuinely live at the same time; Alpha improves the former and does not
  permit the latter;
- compile the candidate with the project's configured compiler rather than
  reasoning from remembered borrow-checker folklore.

Polonius Alpha does not remove ownership requirements at suspension, task,
thread, process, or serialization boundaries. Read
[polonius-alpha.md](../rust-router/references/polonius-alpha.md) for the shared
project-posture test and semantic boundary.

## Red flags

- clones multiply each time the borrow checker complains,
- `Rc` or `Arc` shows up where one owner plus borrowed readers would do,
- `Arc<Mutex<T>>` appears before the real sharing pattern is known,
- references are stored where owning data would simplify the type,
- resource release depends on "remember to call close()",
- `'static` is used to silence a lifetime problem instead of explaining one.

Read [borrow-and-own-patterns.md](references/borrow-and-own-patterns.md) for
API choices, [interior-mutability.md](references/interior-mutability.md) for
shared mutation, [lifecycle-and-raii.md](references/lifecycle-and-raii.md)
for resource scope patterns, and
[encapsulation-and-raii.md](references/encapsulation-and-raii.md) for
ownership as an architectural lever and the `Mutex`/`MutexGuard`/`Drop`
wireframe.
