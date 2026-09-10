# Verus project on-ramp

Verus is the least-adopted of the three tools in the estate, and the
review history of the repositories that did adopt it is mostly about
tooling rather than proofs. This page lists the shape that avoids those
findings; the survey behind it is `docs/verification-review-failure-modes.md`.

## 1. Decide whether Verus is due yet

Verus arrives last. The repositories that adopted it well did so only
after Kani harnesses and property tests existed and a pure kernel had
been extracted: "Verus should arrive only after there is something small
and stable enough to prove". Good first targets are local algebraic
invariants close to pure predicates (a config constructor's
canonicalization, an ordering relation, a pair-normalization). Poor first
targets are anything whose proof depends on collection internals or
bit-level mixing.

## 2. Pin and install

```text
tools/
├── verus/
│   ├── VERSION          # e.g. 0.2026.05.24.ecee80a
│   ├── SHA256SUMS       # <sha256>  verus-<version>-x86-linux.zip
│   └── README.md        # what is pinned and how to bump it
└── rust-prover-tools/
    └── REF              # prover-tools commit pin (shared with Kani)
```

```bash
prover-tools verus install --repo-root .
prover-tools verus run --repo-root . --proof-file verus/my_proofs.rs
```

`install` downloads the pinned release, verifies it against
`SHA256SUMS`, and unpacks to `.verus/<version>/verus`. `run` resolves the
binary, reads the Rust toolchain Verus reports from `verus --version`,
installs it through `rustup` only if the probe fails, and streams the
proof output with Verus's exit code preserved. Forward flags such as
`--rlimit` with repeatable `--extra-arg`.

Do not reintroduce a shell wrapper. The retired scripts drew findings
for every one of: no checksum, `$?` captured after a negated `!`
compound (always 0, so the gate never failed), only the last proof
file's status propagated, `trap` handlers overwriting each other, flags
confused with positional file arguments, sibling scripts resolved from
the caller's working directory, `rustup install` versus `rustup
toolchain install`, and Bash 3.2 incompatibilities on macOS.

## 3. Makefile

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
VERUS_PROOF_FILE ?= verus/my_proofs.rs
VERUS_FLAGS ?=

install-verus: ## Install the pinned Verus release
	$(PROVER_TOOLS) verus install --repo-root .

verus: ## Run the Verus proof entry point
	$(PROVER_TOOLS) verus run --repo-root . --proof-file "$(VERUS_PROOF_FILE)" $(VERUS_FLAGS)
```
<!-- markdownlint-enable MD010 -->

`tools/rust-prover-tools/REF` carries one `ref: <40-hex commit>` line
(see the Kani on-ramp for the full file). The REF path is fixed with
`override :=` because it is interpolated into a `$(shell ...)` call:
Make expands variables before the shell runs, so quoting cannot make
an environment-supplied path safe. The guard rejects a missing or
malformed ref before `PROVER_TOOLS_SOURCE` can be left unpinned, and
`PROVER_TOOLS` is locked to the pin-derived source unless
`PROVER_TOOLS_CONTRACT_TEST` is set, which is the seam contract tests
use to substitute a recording fake; production runs cannot repoint it
from the environment.

Keep `verus` out of `make test`, `make lint`, `make all`, and the
pull-request formal gate until the proofs have been stable for a while;
run it from a scheduled job or on demand. Redact `VERUS_FLAGS` before
echoing a command. Where a proof set is not yet written, ship the target
as an explicit `FORMAL-SKIP` stub rather than a target that succeeds
silently.

## 4. Layout

```text
project/
├── Cargo.toml
├── src/
│   └── ordering.rs               # production code
└── verus/
    ├── my_proofs.rs              # root: spec types, top-level lemmas, mod decls
    ├── my_proofs_ordering.rs     # one file per property family
    └── my_proofs_extract.rs
```

Verus compiles its own files; production modules cannot be `use`d. Two
bridges exist and both need maintenance:

- **Spec mirror.** Re-declare the production struct as a `spec` type and
  keep it in sync by review. Document, on each spec item, which runtime
  type and function it models; spec items are public API.
- **`#[path]` import.** Pull a production type in directly. Then add a
  CI check (a script or test) asserting that the path and the referenced
  type still exist, because nothing else will notice a rename.

Either way, a proof over an idealized structure (`Seq<nat>`) says nothing
about a differently shaped runtime structure (`BTreeMap`) until an
explicit refinement lemma connects them. Reviewers look for the bridge,
not just the lemma.

## 5. Lint and documentation policy

- `#[allow]` is forbidden in `verus/` exactly as in production. Use
  `#[expect(dead_code, reason = "...")]` on the specific spec-only item;
  never a module-level blanket.
- Every file starts with a `//!` comment; every `pub(super) proof fn`
  carries `///` rustdoc stating the property in words.
- Keep ExecPlan `Status:` fields, ADR text, and the developers' guide
  proof inventory in agreement with the files; document what each proof
  does not cover.
- Follow en-GB-oxendict spelling in `tools/verus/README.md` too.

## 6. Contract tests

Repositories gate the shape with tests: non-empty `VERSION` and
`SHA256SUMS`, a checksum row naming the configured archive, a REF file
with a 40-character commit, Makefile recipes that delegate through
`$(PROVER_TOOLS)` and contain no `curl`, `unzip`, `sha256sum`, or
`rustup toolchain install`, and a dry-run asserting the exact
`prover-tools verus run --proof-file ...` invocation with a recording
fake executable rather than `echo`. Tests exercise the seam with
`PROVER_TOOLS_CONTRACT_TEST=1 PROVER_TOOLS=<fake>` on the `make`
command line.
