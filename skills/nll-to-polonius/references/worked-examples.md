# Worked examples: hypotheses and controlled evidence

The original July 2026 notes discussed weaver, netsuke, ddlint, stilyagi, and
lille. They did not include immutable source revisions and paired compiler logs
for their proposed rewrites. Treat W1-W5 below as historical source-review
examples, not verified migration results or current repository inventories.
Reinspect the actual source and consumers before acting.

A clone count or an absence of raw borrow errors does not establish that NLL
caused an architecture. Classify the proposed replacement, compare the best
compatible alternative, and preserve the caller's real semantics. W6 supplies
the separately archived compiler evidence from Peregrine's design PR.

## W1: netsuke graph view, an owned entry key

The historical `src/graph_view/mod.rs` example was:

```rust
for input in &edge.inputs {
    node_paths.entry(input.clone()).or_insert(NodeKind::Source);
}
```

**Local finding:** this write-only insertion already works under NLL. A
`contains_key` guard followed by insertion can avoid owning the key on hits
without returning a borrow. It trades hit-path key construction against
additional miss-path lookup work; measure the relevant workload.

**API hypothesis:** a reference-returning get-or-create helper may be useful if
real callers subsequently need access to the stored node kind. Its early
borrowed-return implementation is a candidate for an explicit off/next
comparison. Do not add an unused `&mut NodeKind` result merely to manufacture a
Polonius dependency, or tag the helper as verified without compiling it.

## W2: weaver plugin registry, registration and duplicate errors

The historical `crates/weaver-plugins/src/registry/mod.rs` example validated a
manifest, rejected an existing name, normalized languages, and inserted the
manifest. It returned `Result<(), PluginError>`.

**Local finding:** duplicate detection followed by insertion does not itself
need Polonius.

**API hypothesis:** returning the inserted manifest might simplify callers that
actually need it. An entry-based implementation can return a reference under
NLL. Likewise, a lookup whose occupied branch returns only an **owned error**,
rather than a reference into the registry, does not establish the
conditional-escaping-borrow problem. Compile the complete proposed method.

Do not change duplicate errors into idempotent `get_or_register` behaviour as
an ownership cleanup. Preserve validation order, error details, and
normalization semantics in both alternatives. A different error type that
borrows registry state is a separate proposal requiring its own evidence.

## W3: netsuke action interning, an identity that is data

The historical `src/ir/from_manifest_support.rs` example was:

```rust
if !actions.contains_key(hash.as_str()) {
    actions.insert(hash.clone(), action);
}
Ok(hash)
```

**Local finding:** no escaping map borrow appears in this expression.

**API finding:** the hash serves as the action's persistent identity in the
intermediate representation. Returning a reference is not a substitute for that
identity. An additional borrowed accessor needs a demonstrated caller, not a
desire to eliminate ID-shaped results. Retain the semantic reason in the audit;
do not invent a compiler rejection for a design choice.

## W4: weaver session access, absence is an error

The historical `crates/weaver-lsp-host/src/host.rs` example was:

```rust
let session = self.sessions.get_mut(&language)
    .ok_or_else(|| LspHostError::unknown(language))?;
Self::ensure_initialized(language, session, overrides)
```

**Local finding:** the error construction in this sketch does not borrow
`self`; an absent session produces an error rather than triggering creation. It
is not evidence of a workaround.

**Future-feature hypothesis:** lazy session creation could introduce a
conditional borrowed return followed by insertion. That would need a real
feature requirement, a compatible alternative, and paired compiler evidence. Do
not change pre-registration policy as part of this audit. A possible future
feature is not a current benefit justifying compiler adoption.

## W5: lille framework write queries and independently scheduled work

The historical `src/dbsp_sync/output.rs` notes described ECS write queries
interleaved with world-handle operations. Inspect the framework's access and
guard contracts before changing references: an apparent workaround may enforce
aliasing or scheduling invariants. The notes alone do not prove that every
borrowed alternative fails.

Owned messages can preserve lifetimes across a daemon turn or detached job.
That does not imply references are forbidden across every `.await` or thread
boundary. Scoped borrowing remains available when owners outlive their users.
Name the actual lifetime, overlap, or snapshot requirement in any refusal.

## W6: Peregrine design PR, controlled checker and solver comparisons

[Peregrine PR #6][pr] proposed an ownership experiment and archived eight
complete compiler fixtures. Read the [ownership comparison][experiment] and
[probe archive][archive] at immutable commit
`3d9a2bd9f7137e38d3f5eb5835f0364be9a82036`.

The archive records results observed on 2026-09-20 using `nightly-2026-08-27`,
`rustc 1.100.0-nightly` (`bff8e12ff5e6bcd53dfb1dbccdcec80a60a856ed`), edition
2024. It explicitly selected `off`/`next` and `no`/`globally`, producing 32
outcomes. The summary below reports that historical evidence; it is not a new
execution by this skill update.

| Fixture                                         | NLL, either solver | Alpha, either solver |
| ----------------------------------------------- | ------------------ | -------------------- |
| Fallible optional cache, branch before borrow   | Pass               | Pass                 |
| Fallible optional cache, early returned borrow  | E0502              | Pass                 |
| Map cache, standard entry API                   | Pass               | Pass                 |
| Map cache, early borrowed hit and entry on miss | E0499              | Pass                 |
| Map cache, contains-key then get-mut            | Pass               | Pass                 |
| Disjoint-field async phase view                 | Pass               | Pass                 |
| Native async method through a trait object      | E0038              | E0038                |
| Overlapping mutable borrows                     | E0499              | E0499                |

The archive also records failure/retry/hit assertions for the successful paired
cache programs. The contains-key alternative and phase-view example are
compile-only controls. These runs do not validate a full framework, executor
`Send` guarantees, consumer support, or runtime performance.

**What the experiment demonstrated:** particular early-return cache
implementations gained acceptance under Alpha. Neither the phase-view
architecture nor the new trait solver caused that acceptance difference.

**What the alternatives reveal:** standard `Entry` already returns a borrow
without cloning the stored payload. The early-return map implementation avoids
owning a key on a hit but adds a lookup on a miss. Both optional-cache
implementations return a borrow without copying the payload; for infallible
initialization, `get_or_insert_with` is an additional compatible alternative.
Do not present these controls as a clone-heavy baseline defeated by a wholly
new ownership model.

**Rules carried into this skill:** give both compiler candidates the same
architectural improvements; select both experimental dimensions explicitly;
retain negative controls; separate compile, behaviour, support, and performance
evidence. An unflagged current nightly is not an old-checker baseline.
Comparison fixtures do not require two maintained production implementations.

## Method summary

1. Use source inspection and the scanner to locate candidates, not diagnose
   NLL pressure from clone counts or API shapes alone.
2. Establish actual caller requirements and the best compatible alternative.
3. Compare the replacement under explicit controls and inspect diagnostics.
4. Keep checker-independent improvements, genuine checker-dependent gains,
   unsupported formulations, and untested ideas in separate categories.
5. Preserve contracts and report scope limitations. An audit can find useful
   work without finding a reason to change compiler support.

[pr]: https://github.com/leynos/peregrine-web/pull/6
[experiment]: https://github.com/leynos/peregrine-web/blob/3d9a2bd9f7137e38d3f5eb5835f0364be9a82036/docs/polonius-ownership-experiment.md
[archive]: https://github.com/leynos/peregrine-web/blob/3d9a2bd9f7137e38d3f5eb5835f0364be9a82036/docs/compiler-probe-evidence.md
