# Worked examples: audit and evolution transcripts

Transcripts from a July 2026 audit of five pre-0.1.0 application codebases
(github.com/leynos: weaver, netsuke, ddlint, stilyagi, lille), all
self-consumed — mode E applies throughout. Each site gets two verdicts:
the **local** verdict (does this exact code fail NLL?) and the
**evolution** verdict (what does the owning API become under the playbook
in `references/api-evolution.md`?). The local verdicts are mostly
negative, and tautologically so: code built under NLL compiles under NLL.
The evolution verdicts carry the value.

A structural finding frames all of them: none of the five codebases
contains a raw NLL problem-case-3 error site, because the house style
avoids reference-returning APIs almost entirely — weaver alone carries
roughly 400 `clone()` calls, and lookups hand back owned values or ids.
That absence is the NLL accommodation. The audit's job in mode E is to
find where the accommodation lives at the API layer, using the local
suspects as entry points.

## W1 — netsuke, `src/graph_view/mod.rs`: entry with cloned key

```rust
for input in &edge.inputs {
    node_paths.entry(input.clone()).or_insert(NodeKind::Source);
    ...
}
```

**Local verdict:** compiles under NLL; the write-only guard could even be
`contains_key`+`insert` today. Not a workaround in itself.

**Evolution verdict:** the loop clones a `Utf8PathBuf` key per input per
edge, hit-dominant once the graph is dense — pure §1.1 pressure. Give the
node-path registry a `fn ensure(&mut self, path: &Utf8Path, kind: NodeKind)
-> &mut NodeKind` accessor in the get-or-create form (clone on miss only)
and route the three sibling `entry(x.clone())` sites (lines ~194, ~213,
~227) through it. The accessor's early-return form fails NLL and passes
Polonius — tag `POLONIUS(case-3)`. Later classification logic that
re-looks-up node kinds can then mutate through the same accessor instead
of re-hashing.

## W2 — weaver, `crates/weaver-plugins/src/registry/mod.rs`: register

```rust
pub fn register(
    &mut self,
    mut manifest: PluginManifest,
) -> Result<(), PluginError> {
    manifest.validate()?;
    let name = manifest.name().to_owned();
    if self.manifests.contains_key(&name) {
        return Err(PluginError::Manifest {
            message: format!("plugin '{name}' is already registered"),
        });
    }
    manifest.normalise_languages();
    self.manifests.insert(name, manifest);
    Ok(())
}
```

**Local verdict:** compiles under NLL; the double lookup is a
duplicate-detection idiom.

**Evolution verdict:** the registry is the textbook §1.1 aggregate. The
NLL-era shape returns `()` and forces every caller that wants the
registered manifest to call `get` again (a second hash) or to have cloned
what it needed before handing the manifest over. Evolve to:

```rust
pub fn register(&mut self, mut manifest: PluginManifest)
    -> Result<&mut PluginManifest, PluginError>
{
    manifest.validate()?;
    let name = manifest.name().to_owned();
    if let Some(_existing) = self.manifests.get(&name) {
        return Err(PluginError::Manifest {
            message: format!("plugin '{name}' is already registered"),
        });
    }
    manifest.normalise_languages();
    self.manifests.insert(name.clone(), manifest);
    Ok(self.manifests.get_mut(&name).expect("just inserted"))
}
```

and audit callers for post-registration re-lookups and pre-registration
clones that the returned borrow now supplies. Whether the final form needs
Polonius depends on how the error arm evolves (an error type borrowing
registry context is §1.2); run the phase-4 classification per the
workflow and tag accordingly. A `get_or_register` variant for idempotent
plugin loading is the natural follow-on and is unambiguously
fail-NLL/pass-Polonius.

## W3 — netsuke, `src/ir/from_manifest_support.rs`: action interning

```rust
if !actions.contains_key(hash.as_str()) {
    actions.insert(hash.clone(), action);
}
Ok(hash)
```

**Local verdict:** compiles under NLL.

**Evolution verdict:** the hash *is* data — it goes into the IR as the
action's persistent identity — so by §1.2 of the playbook the id-returning
shape is correct and stays. The evolution is narrower: an
`fn intern(&mut self, action: Action) -> Result<(&ActionHash, &Action)>`
form would return the canonical entry and stop the caller-side re-lookups,
but only if callers actually need the interned value back; at present they
need only the hash. **Refuse for now**, tag
`POLONIUS-REFUSED(id-is-data)`, revisit if the interner grows lookup
traffic. Refusals like this one are what keep mode E from becoming
reference-mania.

## W4 — weaver, `crates/weaver-lsp-host/src/host.rs`: session access

```rust
let session = self.sessions.get_mut(&language)
    .ok_or_else(|| LspHostError::unknown(language))?;
Self::ensure_initialized(language, session, overrides)
```

**Local verdict:** compiles under NLL — `language` is Copy, the error
closure borrows nothing from `self`, and absent sessions are an error
rather than a creation trigger.

**Evolution verdict:** this is the site closest to the canonical target
shape, held back only by its error-not-create policy. The moment the host
gains lazy session spawning — the obvious direction for an LSP host that
currently requires pre-registration — the natural form is exactly
api-evolution.md §1.1:

```rust
fn session(&mut self, lang: Language) -> Result<&mut Session, LspHostError> {
    if let Some(s) = self.sessions.get_mut(&lang) {
        return Ok(s);
    }
    let s = Session::spawn(lang, &self.overrides)?;
    self.sessions.insert(lang, s);
    Ok(self.sessions.get_mut(&lang).expect("just inserted"))
}
```

fail-NLL/pass-Polonius (the early return extends the loan across the
spawn-and-insert under NLL). Record as a design note in the tracking
document so the lazy-spawn feature lands in the direct form rather than
recapitulating the double-lookup era.

## W5 — lille, `src/dbsp_sync/output.rs`: framework write-queries

ECS write-queries (`write_query.get_mut(entity)`) interleaved with world-
handle mutation.

**Local and evolution verdict:** refuse both. The framework's query and
handle types mediate aliasing between systems — api-evolution.md §2.1.
Introducing long-lived references across DBSP handle operations fights the
framework's own discipline. Tag any tempting site
`POLONIUS-REFUSED(aliasing)` and move on. Likewise weaverd's daemon paths:
owned messages across event-loop turns are §2.2, permanent.

## Method summary

1. The scanner produces local suspects and design-pressure hotspots.
2. Local classification (patterns.md §5) settles what the *existing code*
   needs — in NLL-built codebases, usually nothing.
3. Evolution classification (api-evolution.md's organizing question)
   settles what the *owning API* becomes. Expect the split seen above:
   two direct targets (W1, W2), one design note for a future feature
   (W4), two principled refusals (W3, W5).
4. Every verdict — especially the refusals — goes into the tracking
   document with the constraint named, so the next pass starts from
   conclusions rather than re-running the argument.
