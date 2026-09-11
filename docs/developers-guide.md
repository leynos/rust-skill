# Developers' guide

This guide covers working on this repository: the Markdown skill
catalogue itself, its manifest gates, and the Python test suite. It does
not cover using the skills; see [Users' guide](users-guide.md) for that.

## Prerequisites

- `uv`, for resolving and running the pinned `dev` dependency group.
- `markdownlint-cli2` and `nixie` on `PATH`. These are external tools, not
  Python dependencies, and the lint gates call them directly.

`pyproject.toml` sets `requires-python = ">=3.12"` and
`[tool.uv] package = false`: the repository is not an installable package,
only a source of validation tooling for the catalogue.

## Getting started

`uv.lock` is committed, so `uv run --group dev <tool>` resolves the pinned
versions of every `dev` dependency with no separate installation step. The
`dev` group supplies four packages:

- `pytest` — the test runner.
- `pyyaml` — parses `SKILL.md` frontmatter in the manifest tests, so the
  assertions inspect YAML values rather than raw text.
- `skills-ref` — validates a skill directory against the Agent Skills
  schema. It is pinned to a commit of the `agentskills` repository rather
  than to a release.
- `yamllint` — lints the YAML frontmatter of each `SKILL.md`.

## The gates

The `Makefile` sets no `.DEFAULT_GOAL` and has no combined `check` target,
so run `make lint` and then `make test` before committing. Run the gates
sequentially rather than in parallel: the manifest targets resolve their
tools through `uv`, and a sequential run benefits from the shared cache.

| Target | What it does |
| --- | --- |
| `make markdownlint` | Lint every Markdown file |
| `make nixie` | Validate every Mermaid diagram |
| `make lint` | Run markdownlint, nixie, and manifests |
| `make skill-frontmatter-lint` | Lint each manifest's YAML frontmatter |
| `make skill-metadata-lint` | Reject non-string metadata keys and values |
| `make skill-manifest-validate` | Run `skills-ref validate` per skill |
| `make skill-manifest-check` | Aggregate the three manifest targets |
| `make test` | Run `pytest` via `uv` |

`make lint` is the whole lint gate: it runs `markdownlint`, `nixie`, and
`skill-manifest-check`. `make skill-manifest-check` in turn aggregates
`skill-frontmatter-lint`, `skill-metadata-lint`, and
`skill-manifest-validate`.

## The skill manifest contract

Every `skills/<name>/SKILL.md` carries YAML frontmatter as its Agent Skills
manifest, and the manifest `name` must equal the skill directory name: a
strict loader discovers a skill by its directory and identifies it by its
manifest.

The frontmatter may only use the keys the Agent Skills schema admits:
`name`, `description`, `license`, `allowed-tools`, `metadata`, and
`compatibility`. Put anything else under `metadata`.

`make skill-frontmatter-lint` extracts each manifest's frontmatter block
with `awk` and pipes it through `yamllint`, so a parse error fails the
gate rather than reaching a strict loader. `make skill-manifest-validate`
runs `skills-ref validate` over each skill directory, checking the fields
against the schema.

`metadata` must be a mapping of strings to strings. `skills-ref` coerces
every value with `str(v)` rather than rejecting other shapes, so a list or
mapping value would pass schema validation but reach consumers as a Python
repr. `make skill-metadata-lint` runs `tools/check_metadata.py` ahead of
validation to reject non-string keys and values. Encode multi-valued
entries — such as the `globs` pattern hints — as a single comma-separated
string; `tests/test_skill_manifests.py` guards those values.

The manifest targets iterate `SKILL_DIRS`, which defaults to every
directory under `skills/` that contains a `SKILL.md`. Override it to check
one skill or a test fixture:

```bash
make skill-manifest-check SKILL_DIRS=skills/kani/
```

## What the tests cover

The test suite lives in `tests/`. `tests/test_skill_manifests.py` runs the
real `Makefile` in the checkout through `uv`, so it needs the real
`pyproject.toml` and `uv.lock` rather than a scratch repository. It writes
its fixtures into a temporary directory rather than committing them, and
passes `SKILL_DIRS` to pin a run to one fixture.

The manifest tests assert that every shipped skill satisfies the contract,
and that `make lint` still enforces it: removing the
`skill-manifest-check` prerequisite would otherwise disable validation
silently. Fixtures cover an absent or empty `name`, a `name` that disagrees
with its directory, and `metadata` entries that are sequences, mappings,
scalars, or non-string keys. One test also pins the relocated
`metadata.globs` strings, so a dropped, reordered, or truncated pattern
fails the suite.

The suite also guards the specialist invocation policy. Every skill but
the router ships an `agents/openai.yaml` setting
`policy.allow_implicit_invocation: false`, which keeps routing with
`rust-router`; one test asserts that over every other shipped skill,
failing on a missing file as well as on a `true` value, and a second
asserts the router has not opted out itself, which would leave the
catalogue reachable only by an explicit invocation. Fixtures pin the
policy reader's failure modes: an absent file reads as no policy,
whereas a malformed document, a non-mapping document, and a non-mapping
`policy` value each fail distinctly rather than reading as absent. That
file is not part of the Agent Skills manifest, so `skills-ref` does not
see it and the `make lint` targets cannot cover it.
