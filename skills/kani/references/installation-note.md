# Installation note: Kani via rust-prover-tools

The previous in-repository install scripts have been replaced by
[`rust-prover-tools`](https://github.com/leynos/rust-prover-tools). The
new tool provides a small CLI (`prover-tools`) that handles version
pinning, installation, and version checks for both Kani and Verus.

## Canonical commands

```bash
# Install the pinned Kani verifier (runs cargo install kani-verifier
# against the pinned version, then cargo kani setup).
prover-tools kani install

# Confirm the installed Kani matches the pin.
prover-tools kani check-version
```

The default version source is `<repo-root>/tools/kani/VERSION` (or
similar; see `--version-file`). Override with `--version` for one-off
checks. The full flag set is documented in the
[cli.py module](https://github.com/leynos/rust-prover-tools/blob/main/rust_prover_tools/cli.py)
and is also accessible via `prover-tools kani install --help`.

The same flags are accepted via `INPUT_*` environment variables (for
example, `INPUT_REPO_ROOT`, `INPUT_VERSION_FILE`) for CI integration, and
the legacy `KANI` environment variable is preserved as the override for
the Kani command name in `check-version`.

## Why this exists

The upstream Kani install step (`cargo install --locked kani-verifier &&
cargo kani setup`) is fine for a one-off install, but project CI needs:

- a single pinned version recorded in-tree so reviewers can see and
  update it,
- a check that confirms the running Kani matches the pin before any
  proofs run,
- a uniform interface that covers both Kani and Verus rather than two
  separate ad hoc scripts.

`rust-prover-tools` provides those without forking install logic into
every project that uses Kani.

## Fallback

If `prover-tools` is not available (for example, on a contributor's
laptop without the Python toolchain), the upstream commands still work:

```bash
cargo install --locked kani-verifier
cargo kani setup
```

Use the fallback only when `prover-tools` cannot be installed. The two
routes can drift in pinned version, so prefer the pinned route in CI and
shared environments.
