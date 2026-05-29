# Misuse-Resistant APIs

The goal is to make the wrong call shape fail to compile and the right one
read like prose. Three patterns and one tooling family carry most of the
load.

## Typestate

Encode the legal call order in the type. A `Builder` returns a
`Configured` which exposes `connect()`; the `Connection` exposes `query()`;
the `Query` exposes `execute()`. Each transition consumes `self` and
returns the next state. Out-of-order calls do not type-check.

Use typestate when:

- the operation order is small and important (open/close, lock/unlock,
  begin/commit/rollback, build/seal/freeze),
- a misuse can corrupt data or leak resources, and a runtime panic is too
  late to help.

Avoid typestate when:

- the legal transitions are a large state machine (the type explosion
  outweighs the safety benefit),
- consumers commonly want to express "any valid state" (each typestate
  step needs its own trait bound).

## Newtype with hidden inner

Wrap a primitive (or another type) in a tuple struct and keep the field
private. The wrapper carries the invariant (`NonEmpty<Vec<T>>`,
`UserId(u64)`, `SanitisedPath`, `MillisSinceEpoch`). Public construction
must go through a constructor that enforces the invariant; the inner value
is accessible only through methods that preserve it.

The relevant API Guidelines tags are `C-NEWTYPE-HIDE` (newtypes encapsulate
implementation) and `C-STRUCT-PRIVATE` (struct fields are private by
default).

## Anti-boolean-blindness

`fn copy(src: &Path, dst: &Path, overwrite: bool, follow_symlinks: bool)`
is a call-site puzzle. Two related fixes:

- Replace each boolean with a domain enum
  (`Overwrite::IfExists` / `Overwrite::Never`,
  `Symlinks::Follow` / `Symlinks::Preserve`). The call site reads as the
  decision it makes.
- For options that combine, pass an `Options` struct constructed by a
  builder. Defaults are explicit; additions do not shuffle the parameter
  list and do not break SemVer for callers that used named-init syntax.

Treat any public function with two or more bool parameters as a red flag.

## API Guidelines worth tagging

The full guidelines are large; the ones most relevant to encapsulation:

- `C-SEALED` (downstream cannot impl your trait without opting in),
- `C-NEWTYPE-HIDE` (newtypes hide their inner type),
- `C-SMART-PTR` (smart-pointer types implement `Deref` rather than
  exposing methods that look like pointer arithmetic),
- `C-STRUCT-PRIVATE` (struct fields are private; access goes through
  methods).

## SemVer tooling

Once a crate ships a public API, regressions are mechanical to detect:

- [`cargo-semver-checks`](https://github.com/obi1kenobi/cargo-semver-checks)
  diffs the public API between two versions and flags breaking changes
  before they land.
- [`cargo-public-api`](https://github.com/Enselic/cargo-public-api) prints
  the public surface; pair it with code review or a CI check that compares
  the snapshot against the last release.

Run one or both in CI on the release branch. They cannot replace a SemVer
judgement call (some breaking changes are deliberate), but they make the
question impossible to overlook.
