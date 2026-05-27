# Installation note: Verus via rust-prover-tools

The previous in-repository install and run scripts have been replaced by
[`rust-prover-tools`](https://github.com/leynos/rust-prover-tools). The
new tool provides a small CLI (`prover-tools`) that handles version
pinning, checksum verification, toolchain installation, and proof
execution for both Kani and Verus.

## Canonical commands

```bash
# Install the pinned Verus release for this target.
prover-tools verus install

# Run Verus against a proof file (preserves Verus's exit code).
prover-tools verus run --proof-file verus/my_proofs.rs
```

`install` downloads the release matching the in-tree pin, verifies its
SHA-256 against the in-tree checksum file, and unpacks it into the
install directory. Defaults: `<repo-root>/tools/verus/VERSION` and
`<repo-root>/tools/verus/SHA256SUMS`; override with `--version-file`,
`--checksum-file`, `--repo-root`, `--install-dir`, or `--target`.

`run` resolves the Verus binary (from `--verus-bin`, the install
directory, then `PATH`), ensures the required Rust toolchain is
installed via `rustup`, and executes the proof file. Repeatable
`--extra-arg` values are appended after the proof file so callers can
forward flags such as `--rlimit` to Verus.

The same flags are accepted via `INPUT_*` environment variables (for
example, `INPUT_REPO_ROOT`, `INPUT_VERSION_FILE`, `INPUT_PROOF_FILE`)
for CI integration. The full flag set is documented in the
[cli.py module](https://github.com/leynos/rust-prover-tools/blob/main/rust_prover_tools/cli.py)
and is also accessible via `prover-tools verus install --help` and
`prover-tools verus run --help`.

## Why this exists

Verus is distributed as prebuilt binaries with per-platform archives,
and proof execution depends on a specific Rust toolchain. Project CI
needs:

- a single pinned version recorded in-tree so reviewers can see and
  update it,
- checksum verification that matches the pin before the archive is
  unpacked,
- automatic provisioning of the toolchain Verus expects, so proof runs
  do not silently use the wrong `rustc`,
- a uniform interface that covers both Kani and Verus rather than two
  separate ad hoc scripts.

`rust-prover-tools` provides those without forking install logic into
every project that uses Verus. The previous `install-verus.sh` and
`run-verus.sh` helpers have been retired.

## No fallback

Unlike Kani (which has a stable upstream `cargo install` route), Verus
does not publish a comparable single-command installer that handles
version pinning, checksums, and the required Rust toolchain. Use
`prover-tools verus` everywhere; do not reintroduce the retired shell
scripts.
