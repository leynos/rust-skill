# Compiler comparison and attribution protocol

Use this protocol for every claimed checker-dependent improvement. It
addresses the confounded comparisons exposed by the
[Peregrine ownership experiment][peregrine]. The experiment's compiler
fixtures are controls, not a second supported production implementation.

## 1. Establish identity and isolate the variables

Choose one dated nightly that supports both `-Zpolonius=off` and
`-Zpolonius=next`. The commands below use `nightly-2026-08-27`, the compiler
in the archived Peregrine evidence, not a recommendation to adopt that
version. Record `rustc -Vv` through that toolchain, source revision, edition,
target, features, lockfile, and complete commands. Verify supported flag
values before running. A rejected flag is not a rejected Rust program.

The [upstream tracking issue][status] dates the Alpha nightly default to
`nightly-2026-08-06`. Omitting `next` does not select NLL on those nightlies.
Even on an earlier compiler, removing an environment override may expose a
configured flag rather than remove it.

Keep solver selection fixed for an ordinary checker comparison. To claim a
benefit from the new trait solver, test all four pairs:

| Checker | Solver | Purpose |
| --- | --- | --- |
| `off` | `no` | NLL and old-solver control |
| `off` | `globally` | Solver change without Alpha |
| `next` | `no` | Alpha without the solver change |
| `next` | `globally` | Both changes |

Keep representations, ownership boundaries, and dispatch strategy equal
between the compiler candidates. Give both the same field-splitting or
phase-view improvement. Evaluate architectural changes separately.

## 2. Complete dependency-free controls

The checked-in fixtures are compile-only controls. They establish neither
runtime behaviour nor future `Send` bounds. Read the archived Peregrine
fixtures for fallible-cache failure/retry/hit assertions and stronger
compatible alternatives:

- [`case3.rs`](fixtures/case3.rs): conditional escaping borrow.
- [`compatible.rs`](fixtures/compatible.rs): standard API and disjoint borrows
  across await.
- [`alias.rs`](fixtures/alias.rs): genuinely overlapping exclusive borrows.

### Run and retain every cell

Direct `rustc` does not consume Cargo's `RUSTFLAGS` or `.cargo/config.toml`.
It isolates these small fixtures from Cargo flag precedence; it does not
establish the effective checker used by a real Cargo build. Run the example
from this reference's directory, or set `POLONIUS_FIXTURES` to the checked-in
fixture directory.

<!-- polonius-rustc-matrix -->

```bash
set -euo pipefail
toolchain=nightly-2026-08-27
out=$(mktemp -d)
fixture_dir=${POLONIUS_FIXTURES:-fixtures}
rustc "+$toolchain" -Vv >"$out/compiler.txt"
printf 'fixture\tchecker\tsolver\texit\n' >"$out/results.tsv"
for fixture in case3 compatible alias; do
  for checker in off next; do
    for solver in no globally; do
      name="$fixture-$checker-$solver"
      args=("+$toolchain" --edition=2024 --crate-type=lib --emit=metadata
            "-Zpolonius=$checker" "-Znext-solver=$solver"
            "$fixture_dir/$fixture.rs" -o "$out/$name.rmeta")
      printf '%q ' rustc "${args[@]}" >"$out/$name.command"
      printf '\n' >>"$out/$name.command"
      if rustc "${args[@]}" >"$out/$name.log" 2>&1; then
        status=0
      else
        status=$?
      fi
      printf '%s\t%s\t%s\t%s\n' "$fixture" "$checker" "$solver" \
        "$status" >>"$out/results.tsv"
    done
  done
done
cat "$out/results.tsv"
printf 'Evidence directory: %s\n' "$out"
```

The script deliberately continues after rejected programs and reports raw
statuses. Its own successful completion does **not** mean all cells passed.
Inspect every log. Expected hypotheses for these controls are `case3`
rejected under `off` (E0502), accepted under `next`; `compatible` accepted
under both; and `alias` rejected under both (E0499), with either solver.
Record actual results rather than copying those expectations as observations.
Investigate unexpected acceptance of the aliasing control immediately.

## 3. Run the real Cargo comparison without hidden flag selection

[Cargo's precedence][cargo-flags] is: `CARGO_ENCODED_RUSTFLAGS`, then
`RUSTFLAGS`, then matching target rustflags, then build rustflags. These are
alternative sources, not a list that Cargo always combines. Appending an
`off` flag to `RUSTFLAGS` can do nothing when encoded flags take precedence;
overriding flags can also accidentally remove required linker or `cfg` flags.

Before using the example, inspect project, ancestor, and Cargo-home config,
including `.cargo/config`, `.cargo/config.toml`, `[env]` overrides, target
flags, compiler wrappers, aliases, and CI environment. Assemble all required
non-checker/non-solver flags as separate arguments in `common`. Do not
blindly append conflicting selections or silently discard required flags.
Keep feature, package, target, and profile selections identical.

<!-- polonius-cargo-comparison -->

```bash
set -euo pipefail
toolchain=nightly-2026-08-27
out=$(mktemp -d)
common=() # Fill with the audited, required non-checker/non-solver flags.
rustc "+$toolchain" -Vv >"$out/compiler.txt"
cargo "+$toolchain" -V >"$out/cargo.txt"
printf 'checker\texit\n' >"$out/results.tsv"
for checker in off next; do
  flags=("${common[@]}" "-Zpolonius=$checker" "-Znext-solver=no")
  printf -v encoded '%s\x1f' "${flags[@]}"
  encoded=${encoded%$'\x1f'}
  printf '%q ' "${flags[@]}" >"$out/$checker.flags"
  printf '\n' >>"$out/$checker.flags"
  if CARGO_ENCODED_RUSTFLAGS="$encoded" \
    cargo "+$toolchain" check --locked --all-targets -vv \
      --target-dir "$out/target-$checker" >"$out/$checker.log" 2>&1; then
    status=0
  else
    status=$?
  fi
  printf '%s\t%s\n' "$checker" "$status" >>"$out/results.tsv"
done
cat "$out/results.tsv"
printf 'Evidence directory: %s\n' "$out"
```

This explicitly replaces the highest-precedence rustflags source and keeps
separate output directories, avoiding stale results. Inspect the verbose
compiler commands to confirm the final flag selection and actual compiler,
especially when wrappers or forced environment configuration are present.
A project with independent build directories must isolate those too.

Run the original source and replacement separately, preserving both archives.
For solver attribution, repeat the same Cargo comparison with `globally`.
For docs and doctests, inspect and control `CARGO_ENCODED_RUSTDOCFLAGS`,
`RUSTDOCFLAGS`, and rustdoc configuration separately. A passing `cargo check`
does not validate those paths. Do not print secrets from the environment.

## 4. Classify evidence, not exit codes alone

| Replacement under NLL | Under Alpha | Interpretation |
| --- | --- | --- |
| Accept | Accept | Checker-independent refactor; no Alpha requirement shown |
| Relevant borrow error | Accept | Candidate checker-specific benefit |
| Reject | Reject | This formulation fails; diagnose before redesigning |
| Accept | Reject | Regression or confound; investigate, do not adopt |
| Infrastructure/flag failure | Any | Inconclusive; repair the experiment |
| Not run | Not run | Source-review hypothesis only |

Attribute a difference only when the baseline worked and the diagnostic
points to the proposed replacement's borrow. A crate already containing
Alpha-only code will fail an NLL build for unrelated sites; reduce each new
claim to an isolated, faithful reproducer or compare scoped diagnostics.
Unsupported switches, missing dependencies, linker failures, lints, and ICEs
are not evidence that the replacement needs Polonius.

Nightly with `off` is not a stable or MSRV build. Run the actual supported
stable/MSRV toolchains independently, with appropriate flags and the same
supported targets/features. Do not use `RUSTC_BOOTSTRAP` to claim support.
A passing isolated fixture is not proof of framework, consumer, or editor
compatibility. Compiler acceptance is not a proof of semantic equivalence,
transactional behaviour, cancellation safety, or performance.

Archive commands, source, full logs, statuses, compiler identities, date,
expected diagnostics, behavioural assertions, and scope limitations. Distinguish
executed evidence from inherited historical results. Rerun on toolchain
upgrades; do not freeze an obsolete rejection into a permanent requirement.

[peregrine]: https://github.com/leynos/peregrine-web/blob/3d9a2bd9f7137e38d3f5eb5835f0364be9a82036/docs/polonius-ownership-experiment.md
[status]: https://github.com/rust-lang/rust/issues/160456
[cargo-flags]: https://doc.rust-lang.org/cargo/reference/config.html#buildrustflags
