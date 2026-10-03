# Agent Instructions

Guidance for agents working in this repository. Read this before changing
tracked files.

## Commit gates

Prefer Makefile targets over running commands directly. Run all four commit
gates sequentially rather than in parallel; the `uv`-managed tools share a
cache, and `make test` runs the Polonius compiler controls before pytest.

Run these gates in order before committing:

```bash
make check-fmt
make lint
make typecheck
make test
```

`make lint` runs `markdownlint`, `nixie`, and `skill-manifest-check`.
`make fmt` formats Python in `tests` and `tools` with Ruff, formats Markdown
with `mdtablefix`, and runs `markdownlint-cli2 --fix`. `make check-fmt` checks
Ruff formatting in `tests` and `tools` and runs `mdtablefix --check` over the
tracked and unignored untracked Markdown files. Both targets need `mdtablefix`
0.6.1 or later, and `make markdownlint` lints `**/*.md`, the scope `make fmt`
and CI use. `make typecheck` runs strict mypy on
`tests/test_polonius_protocol.py` and `tests/polonius_compile_matrix.py`; both
tools come from the pinned `dev` dependency group through `uv`. `make test`
requires `rustup`'s `rustc` proxy on `PATH` and the installed
`nightly-2026-08-27` toolchain for its Polonius fixture matrix.

## Changes under `skills/`

Every skill is a directory containing a `SKILL.md` whose YAML frontmatter is an
Agent Skills manifest. The manifest `name` is the discovery name; a skill whose
manifest omits it is not discoverable by a strict loader.

`make lint` depends on `skill-manifest-check`, so the manifest contract is
already enforced by the gate sequence above. When adding, renaming, or editing
anything under `skills/`, the following are required:

- Run all four commit gates above. `make lint` runs
  `skill-frontmatter-lint` (`yamllint` over each extracted frontmatter block)
  and `skill-manifest-validate` (`skills-ref validate` over each skill
  directory). `make test` runs `tests/test_skill_manifests.py`, which asserts
  that every shipped manifest satisfies the contract and that `make lint` still
  enforces it.
- Keep the directory name equal to the manifest `name`.
- Keep the frontmatter to the keys the Agent Skills schema admits: `name`,
  `description`, `license`, `allowed-tools`, `metadata`, and `compatibility`.
  Put anything else under `metadata`.
- Keep `metadata` a mapping of strings to strings. `skills-ref` coerces every
  value with `str(v)` rather than rejecting other shapes, so a list or mapping
  value passes validation but reaches consumers as a Python repr. Encode
  multi-valued entries — such as the `globs` pattern hints — as a single
  comma-separated string.
- Ship `agents/openai.yaml` with `policy.allow_implicit_invocation: false` for
  every skill but `rust-router`, so the router keeps the routing decision.
  `skills-ref` does not read the file, so only `make test` enforces it.

Do not weaken these checks to make a manifest pass. Fix the manifest instead of
excluding it from `SKILL_DIRS` or relaxing the `yamllint` configuration.

To check one skill or a fixture while iterating:

```bash
make skill-manifest-check SKILL_DIRS=skills/kani/
```

## Documentation

Changes that alter skill discovery, installation, or naming belong in
[the users' guide](docs/users-guide.md). Changes to validation tooling,
Makefile targets, or development dependencies belong in
[the developers' guide](docs/developers-guide.md), alongside the manifest
contract they serve. Record notable changes in [the changelog](CHANGELOG.md),
which follows the Common Changelog format.
