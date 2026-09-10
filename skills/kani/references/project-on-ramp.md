# Kani project on-ramp

The shape below is what the estate's reviewers and contract tests expect
when Kani enters a repository. It is distilled from the survey in
`docs/verification-review-failure-modes.md`; each item is there because
its absence drew a review finding.

## 1. Pin the tool in-tree

```text
tools/
├── kani/
│   └── VERSION                 # MAJOR.MINOR.PATCH, e.g. 0.67.0
└── rust-prover-tools/
    └── REF                     # pins the prover-tools commit
```

`tools/rust-prover-tools/REF`:

```text
repository: https://github.com/leynos/rust-prover-tools.git
branch: main
ref: <40-char commit sha>
verify: git fetch --depth 1 https://github.com/leynos/rust-prover-tools.git \
  <sha> && git rev-parse FETCH_HEAD
```

The `verify` command fetches the pinned commit itself and prints the SHA
of what was fetched; compare it to `ref`. Matching a branch such as
`refs/heads/main` proves nothing about the pin.

A pin is only a pin if something checks it. `prover-tools kani
check-version` compares the running `cargo kani --version` against
`tools/kani/VERSION`; run it before any proof. `cargo install --locked
kani-verifier` does **not** pin the verifier release; `--locked` pins the
verifier's dependency tree only.

## 2. Declare the cfg and gate the code

```toml
[lints.rust]
unexpected_cfgs = { level = "warn", check-cfg = ["cfg(kani)"] }
```

Layout options that have passed review, in order of preference:

- a sibling `kani.rs` declared with `#[cfg(kani)] mod kani;` next to the
  code it proves (default path resolution, no `#[path]`),
- an inline `#[cfg(kani)] mod kani_proofs { ... }` at the bottom of the
  module,
- a `*_kani_proofs.rs` file per subsystem.

Shared drivers used by both proptest and Kani live under
`#[cfg(any(test, kani))]` and are `pub(crate)`. Never widen a public API
for proof access; Kani-only `pub(crate)` visibility is acceptable when
documented.

## 3. Makefile targets

Delegate to `prover-tools`; never embed `cargo install`, `cargo kani
setup`, `curl`, `unzip`, `sha256sum`, or `rustup toolchain install` in a
recipe. Contract tests in the estate fail on any of those strings.

<!-- markdownlint-disable MD010 -->
```makefile
override PROVER_TOOLS_REF_FILE := tools/rust-prover-tools/REF
override PROVER_TOOLS_REF := $(shell awk '/^ref:/ { print $$2 }' $(PROVER_TOOLS_REF_FILE))
ifeq ($(shell printf '%s' '$(PROVER_TOOLS_REF)' | grep -Ec '^[0-9a-f]{40}$$'),0)
$(error PROVER_TOOLS_REF missing or malformed; expected "ref: <40-hex>" in $(PROVER_TOOLS_REF_FILE))
endif
override PROVER_TOOLS_SOURCE := git+https://github.com/leynos/rust-prover-tools.git@$(PROVER_TOOLS_REF)
PROVER_TOOLS_CONTRACT_TEST ?=
ifeq ($(PROVER_TOOLS_CONTRACT_TEST),)
override PROVER_TOOLS := uv tool run --from "$(PROVER_TOOLS_SOURCE)" prover-tools
else
PROVER_TOOLS ?= uv tool run --from "$(PROVER_TOOLS_SOURCE)" prover-tools
endif
KANI ?= cargo kani
KANI_FLAGS ?=

install-kani: ## Install the pinned Kani verifier
	$(PROVER_TOOLS) kani install --repo-root .

kani-check: ## Fail if the installed Kani does not match tools/kani/VERSION
	$(PROVER_TOOLS) kani check-version --repo-root . --kani-command "$(KANI)"

kani: kani-check ## Fast smoke tier: named harnesses with tight bounds
	$(KANI) --harness verify_smoke_2_nodes --harness verify_dispatch $(KANI_FLAGS)

kani-full: kani-check ## Every harness; nightly only
	$(KANI) $(KANI_FLAGS)

formal-pr: kani ## Pull-request formal gate
formal-nightly: kani-full ## Scheduled formal gate
```
<!-- markdownlint-enable MD010 -->

Recipes need real tabs. Route the binary through `$(KANI)` and any
`$(CARGO)` variable the repository already defines. If a variable must
come only from a pin file, use `override :=` so an inherited environment
value cannot repoint it. Redact user-supplied `KANI_*_FLAGS` before
echoing a command. Keep `kani` and `kani-full` out of `make test`,
`make lint`, and `make all` unless the repository has decided on a
fail-closed formal gate and documented it. The REF path is fixed with
`override :=` because it is interpolated into a `$(shell ...)` call:
Make expands variables before the shell runs, so quoting cannot make
an environment-supplied path safe. The guard rejects a missing or
malformed `ref:` line before `PROVER_TOOLS_SOURCE` can be left
unpinned. `PROVER_TOOLS` is locked to the pin-derived source unless
`PROVER_TOOLS_CONTRACT_TEST` is set, which is the seam contract tests
use to substitute a recording fake; production runs cannot repoint it
from the environment.

`kani-check` is a prerequisite of each proof target, not only of the
gate, so `make -j` cannot start a proof before the version check
completes.

Until a repository has real harnesses, ship the targets as explicit
stubs that print `FORMAL-SKIP: <target> not yet implemented` and exit
zero unless `FORMAL_STRICT=1`; document the placeholder status plainly
and do not describe a `prover-tools kani run` subcommand, which the
pinned CLI does not expose.

## 4. CI

Two jobs:

- `kani-smoke` on pull requests: path filter covering every manifest the
  gated command compiles (workspace root and each proved crate), the
  harness files, `Makefile`, and `tools/kani/VERSION`; `concurrency`
  group keyed on the ref with `cancel-in-progress: true`;
  `timeout-minutes: 20`–`30`; steps in order restore cache → `make
  install-kani` → `make kani-check` → `make kani`.
- `kani-nightly` on a schedule: its own `concurrency` group, a longer
  timeout, `make kani-full`, and a gate that skips when nothing landed in
  a rolling window (calendar-day equality skips fresh commits; clock skew
  should be a soft skip).

Caching Kani is optional and should be measured; `chutoro` measured a
cold install at about 16 s and removed the cache, `netsuke` caches under
version-qualified paths with a key that hashes every input. If a cache
exists, its predicate must be version-aware and its composite action
must declare the variables it renders the key from.

Kani-conditional steps on heterogeneous runners must probe for
`cargo-kani` and print a visible skip diagnostic. Do not let a failed
stderr write turn a skip into a test failure through `?`: use
`eprintln!`, which panics only if stderr is closed, or ignore the write
error explicitly, rather than `writeln!(stderr)?`.

## 5. Contract tests

The estate gates the shape above with tests rather than convention:

- Makefile tests that run each verification target against a recording
  fake `prover-tools` (a script that logs its arguments; not `echo`, which
  cannot observe recipe-local environment) and assert the exact
  invocation, flag forwarding, redaction, and non-zero exit propagation.
  They set `PROVER_TOOLS_CONTRACT_TEST=1 PROVER_TOOLS=<fake>` on the
  `make` command line; without the flag the pinned source is locked.
- Workflow-contract tests asserting the smoke job's step order by
  position, the cache key inputs, the path filter's manifest list, and
  that both `*.yml` and `*.yaml` are enumerated.
- A `cargo-mutants` exclusion for every `cfg(kani)`-only module (the
  tool does not evaluate the cfg, so their survivors are noise), asserted
  by the workflow-contract test.
- Optionally, mutation evidence: every `#[kani::proof]` owns a patch
  under `docs/verification/mutations/<module__path>.patch` that seeds a
  realistic fault, or an explicit exemption with a reason; orphan patches
  fail; each patch must `git apply --check`, skipped outside a git
  worktree so cargo-mutants copies do not report false kills.
- `trybuild` compile-pass tests for the `cfg(kani)` gating itself.

## 6. Documentation that must move with the code

- A harness inventory table in the developers' guide: harness name,
  module, bounds (N, alphabet, unwind), what is proved, what is not. Every
  harness added, retired, or re-bounded updates it in the same PR.
- Rustdoc on every `#[cfg(kani)]`-only helper stating what it does and
  why it exists (proof tractability, symbolic-state reduction).
- ExecPlan or ADR status fields, checkbox lists, and quoted unwind values
  kept in agreement with the code; reviewers flag each stale value.
- The exact local invocation, including `make kani` and any environment
  the tool needs, derived from `cargo kani --version` rather than a
  contributor's home directory.
