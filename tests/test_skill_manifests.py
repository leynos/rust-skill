"""Contract tests for shipped Agent Skills manifests.

Each shipped skill's `SKILL.md` opens with YAML frontmatter that a strict
loader reads before the skill is usable, and the manifest's `name` is the
identifier discovery resolves. Each specialist skill also ships an
`agents/openai.yaml` opting it out of implicit invocation, leaving the router
as the catalogue's discovery surface. The Makefile targets exercised here are
the ones `make lint` depends on, so a manifest a loader could not use fails
the commit gate rather than reaching an installation untouched.

Unlike a unit test, these run the real Makefile in the checkout: the manifest
targets resolve their tools through `uv run`, which needs the real
`pyproject.toml` and `uv.lock`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SHIPPED_MANIFESTS = sorted((REPO_ROOT / "skills").glob("*/SKILL.md"))

# The router is implicitly invocable, so the catalogue has an entry point; every
# other skill opts out, so routing decisions stay with the router rather than
# competing with the specialist skills it routes to.
ROUTER_SKILL = "rust-router"
IMPLICIT_INVOCATION = "allow_implicit_invocation"

# The pattern hints the eleven relocated manifests must keep. The migration moved
# a legacy top-level `globs` sequence into `metadata.globs` as one comma-separated
# string, so the exact string is the data contract that proves no pattern was
# dropped, reordered, or truncated.
EXPECTED_GLOBS = {
    "arch-crate-design": ("**/Cargo.toml", "**/*.rs"),
    "domain-cli-and-daemons": ("**/Cargo.toml", "**/*.rs"),
    "domain-embedded-and-iot": ("**/Cargo.toml", "**/*.rs", "**/.cargo/config.toml"),
    "domain-web-services": ("**/Cargo.toml", "**/*.rs"),
    "rust-async-and-concurrency": ("**/Cargo.toml", "**/*.rs"),
    "rust-errors": ("**/Cargo.toml", "**/*.rs"),
    "rust-memory-and-state": ("**/Cargo.toml", "**/*.rs"),
    "rust-performance-and-layout": ("**/Cargo.toml", "**/*.rs"),
    "rust-router": ("**/Cargo.toml", "**/*.rs"),
    "rust-types-and-apis": ("**/Cargo.toml", "**/*.rs"),
    "rust-unsafe-and-ffi": ("**/Cargo.toml", "**/*.rs"),
}


def _run_make(target: str, *skill_dirs: Path) -> subprocess.CompletedProcess[str]:
    """Run a Makefile manifest target over shipped skills or given fixtures."""
    arguments = ["make", target]
    if skill_dirs:
        arguments.append("SKILL_DIRS=" + " ".join(f"{directory}/" for directory in skill_dirs))
    return subprocess.run(
        arguments,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _run_manifest_check(skill_dir: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run the Makefile contract check for shipped skills or one fixture."""
    return _run_make("skill-manifest-check", *([skill_dir] if skill_dir is not None else []))


def _frontmatter(manifest: Path) -> dict[str, object]:
    """Parse the YAML frontmatter block of a skill manifest."""
    lines = manifest.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0] == "---", f"{manifest} does not open with a frontmatter fence"
    closing = lines.index("---", 1)
    return yaml.safe_load("\n".join(lines[1:closing])) or {}


def _write_manifest(skill_dir: Path, body: str) -> Path:
    """Create a skill directory containing the given manifest text."""
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    return skill_dir


def _write_openai_config(skill_dir: Path, config: str) -> Path:
    """Create a skill directory containing the given `agents/openai.yaml` text."""
    agents = skill_dir / "agents"
    agents.mkdir(parents=True)
    (agents / "openai.yaml").write_text(config, encoding="utf-8")
    return skill_dir


def _openai_policy(skill_dir: Path) -> dict[str, object] | None:
    """Read the `policy` mapping from a skill's `agents/openai.yaml`.

    The file is optional: the router ships none, and the schema has no bearing
    on it, so a missing file reads as "no policy" rather than as a fixture
    error. A file that is present must still parse as a mapping with a `policy`
    mapping inside it, so a malformed one fails rather than reading as absent.
    """
    config = skill_dir / "agents" / "openai.yaml"
    if not config.is_file():
        return None
    parsed = yaml.safe_load(config.read_text(encoding="utf-8"))
    assert isinstance(parsed, dict), f"{config} is not a YAML mapping"
    policy = parsed.get("policy")
    assert isinstance(policy, dict), f"{config} carries no policy mapping"
    return policy


def test_shipped_skill_manifests_satisfy_the_contract() -> None:
    """Every shipped skill passes YAML and Agent Skills schema validation."""
    result = _run_manifest_check()

    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("case", "frontmatter"),
    [
        ("missing", "description: A fixture that lacks the required discovery name.\n"),
        ("empty", 'name: ""\ndescription: A fixture whose discovery name is empty.\n'),
    ],
)
def test_manifest_check_rejects_an_unusable_name(tmp_path: Path, case: str, frontmatter: str) -> None:
    """A strict loader cannot discover a skill without a usable discovery name.

    An absent `name` and an empty `name` fail discovery identically, so the
    contract must reject both rather than only the absent case.
    """
    skill_dir = _write_manifest(
        tmp_path / f"{case}-name",
        f"---\n{frontmatter}---\n\n# Fixture\n",
    )

    result = _run_manifest_check(skill_dir)

    assert result.returncode != 0, result.stdout + result.stderr


def test_manifest_check_rejects_a_name_that_disagrees_with_its_directory(tmp_path: Path) -> None:
    """A discovery name that differs from the directory name fails the gate.

    `skills-ref` resolves a skill by directory and then checks the manifest
    `name` against it, so a non-empty name that disagrees is as unusable as a
    missing one: the directory a caller copies is not the name it resolves.
    """
    skill_dir = _write_manifest(
        tmp_path / "directory-name",
        "---\nname: manifest-name\n"
        "description: A fixture whose discovery name disagrees with its directory.\n"
        "---\n\n# Fixture\n",
    )

    result = _run_manifest_check(skill_dir)

    assert result.returncode != 0, result.stdout + result.stderr
    assert "must match skill name" in result.stdout + result.stderr, result.stdout + result.stderr


@pytest.mark.parametrize("manifest", SHIPPED_MANIFESTS, ids=lambda path: path.parent.name)
def test_shipped_metadata_values_are_strings(manifest: Path) -> None:
    """Metadata carries only string values, which `skills-ref` silently coerces.

    `skills_ref.parser` rewrites every metadata value with `str(v)`, so a YAML
    sequence survives validation but reaches consumers as a Python repr.  The
    specification permits string keys and string values only, so reject the
    non-conformant shapes here rather than shipping a silently mangled value.
    """
    metadata = _frontmatter(manifest).get("metadata", {})

    assert isinstance(metadata, dict), f"metadata must be a mapping, got {type(metadata).__name__}"
    non_strings = {key: value for key, value in metadata.items() if not isinstance(value, str)}
    assert not non_strings, f"metadata values must be strings: {non_strings}"


@pytest.mark.parametrize(
    "manifest",
    [path for path in SHIPPED_MANIFESTS if path.parent.name != ROUTER_SKILL],
    ids=lambda path: path.parent.name,
)
def test_specialist_skills_disable_implicit_invocation(manifest: Path) -> None:
    """Every skill but the router ships an `agents/openai.yaml` opting it out.

    The router resolves a task to one specialist skill, so an implicitly
    invocable specialist competes with that routing decision. A missing file
    leaves the client's default in place and a `true` value is no better, so
    both fail the contract rather than only the second.
    """
    skill = manifest.parent
    policy = _openai_policy(skill)

    assert policy is not None, f"{skill} ships no agents/openai.yaml"
    assert policy.get(IMPLICIT_INVOCATION) is False, (
        f"{skill} must set {IMPLICIT_INVOCATION}: false, got {policy!r}"
    )


def test_router_keeps_its_own_invocation_policy() -> None:
    """The router stays implicitly invocable, so the catalogue is discoverable.

    The test above opts every specialist skill out, which leaves the router as
    the only entry point. Copying a specialist's configuration onto the router
    would leave the catalogue reachable only by an explicit invocation. The
    exemption is keyed on the router's name, so the name is checked against the
    shipped set first: a rename would otherwise move the exemption to a skill
    that no longer has it.
    """
    router = REPO_ROOT / "skills" / ROUTER_SKILL

    assert (router / "SKILL.md") in SHIPPED_MANIFESTS, (
        f"{ROUTER_SKILL} is not a shipped skill, so the exemption has drifted"
    )

    policy = _openai_policy(router)

    assert policy is None or policy.get(IMPLICIT_INVOCATION) is not False, (
        f"{ROUTER_SKILL} must not disable implicit invocation, got {policy!r}"
    )


def test_openai_policy_reads_an_absent_file_as_no_policy(tmp_path: Path) -> None:
    """A skill that ships no `agents/openai.yaml` has no policy to report.

    An absent file is a valid state rather than an error, because the router is
    exempt from the opt-out. Returning `None` for it is what distinguishes the
    two tests above: a specialist whose configuration is missing must fail the
    contract, while an absent policy on the router must not.
    """
    assert _openai_policy(tmp_path / "absent") is None


# The malformed case's wording is PyYAML's own, pinned by the committed
# `uv.lock`; the other rows pin the assertion each mis-shaped document reaches,
# so an input that stops being rejected as intended fails here.
@pytest.mark.parametrize(
    ("case", "config", "error", "message"),
    [
        ("malformed-yaml", "policy: [unclosed\n", yaml.YAMLError, "expected ',' or ']'"),
        ("empty-document", "", AssertionError, "is not a YAML mapping"),
        ("scalar-document", "false\n", AssertionError, "is not a YAML mapping"),
        ("sequence-document", "- policy\n", AssertionError, "is not a YAML mapping"),
        ("scalar-policy", "policy: false\n", AssertionError, "carries no policy mapping"),
        (
            "sequence-policy",
            "policy:\n  - allow_implicit_invocation\n",
            AssertionError,
            "carries no policy mapping",
        ),
    ],
)
def test_openai_policy_rejects_a_present_but_unusable_config(
    tmp_path: Path, case: str, config: str, error: type[Exception], message: str
) -> None:
    """A configuration that is present but unusable fails rather than reading as absent.

    Only a missing file means "no policy". A malformed or mis-shaped one that
    took the same route would let a specialist satisfy the contract above while
    its configuration is never checked, so each shape must fail, and fail
    distinctly: an unparseable document is a YAML error, whereas one that parses
    to the wrong shape reaches the assertion that describes it.
    """
    skill = _write_openai_config(tmp_path / case, config)

    with pytest.raises(error) as raised:
        _openai_policy(skill)

    assert message in str(raised.value), str(raised.value)


@pytest.mark.parametrize("skill", sorted(EXPECTED_GLOBS), ids=str)
def test_relocated_manifests_keep_every_globs_pattern(skill: str) -> None:
    """The migration preserved every legacy `globs` pattern, in order.

    `metadata.globs` is a single comma-separated string, so a dropped,
    reordered, or truncated pattern shows up as a changed string. Type-checking
    the value is not enough, because an empty string is still a string.
    """
    metadata = _frontmatter(REPO_ROOT / "skills" / skill / "SKILL.md")["metadata"]

    assert isinstance(metadata, dict), f"{skill} must carry a metadata mapping"
    assert metadata["globs"] == ", ".join(EXPECTED_GLOBS[skill])


@pytest.mark.parametrize(
    ("case", "metadata"),
    [
        ("sequence-value", "metadata:\n  globs: [Cargo.toml, Cargo.lock]\n"),
        ("block-sequence-value", "metadata:\n  globs:\n    - Cargo.toml\n    - Cargo.lock\n"),
        ("mapping-value", "metadata:\n  globs:\n    nested: mapping\n"),
        ("scalar-value", "metadata:\n  globs: 7\n"),
        ("non-string-key", "metadata:\n  7: Cargo.toml\n"),
    ],
)
def test_metadata_lint_rejects_non_string_entries(tmp_path: Path, case: str, metadata: str) -> None:
    """A metadata key or value that is not a string fails the metadata target.

    `skills_ref.parser` rewrites both with `str()` rather than rejecting them,
    and the schema validator never inspects the nested field, so without this
    target a manifest could ship a Python repr where consumers expect text.
    """
    skill_dir = _write_manifest(
        tmp_path / f"{case}-fixture",
        "---\n"
        f"name: {case}-fixture\n"
        "description: A fixture whose metadata breaks the string contract.\n"
        f"{metadata}"
        "---\n\n# Fixture\n",
    )

    result = _run_make("skill-metadata-lint", skill_dir)

    assert result.returncode != 0, result.stdout + result.stderr
    assert "metadata" in result.stdout + result.stderr, result.stdout + result.stderr


@pytest.mark.parametrize(
    ("case", "metadata"),
    [
        ("untyped-sequence", "metadata:\n  globs: [Cargo.toml, Cargo.lock]\n"),
        ("untyped-mapping", "metadata:\n  globs:\n    nested: mapping\n"),
    ],
)
def test_lint_rejects_an_untyped_metadata_shape(tmp_path: Path, case: str, metadata: str) -> None:
    """`make lint` fails on a list or mapping metadata value, not just on YAML.

    `skills-ref` coerces such a value with `str(v)`, so schema validation alone
    would pass it; only the metadata target wired into `skill-manifest-check`
    makes `make lint` fail. The fixture is named in the failure output, so a
    failure raised by the Markdown or Mermaid gates cannot pass this test.
    """
    skill_dir = _write_manifest(
        tmp_path / f"{case}-fixture",
        "---\n"
        f"name: {case}-fixture\n"
        "description: A fixture whose metadata value is not a string.\n"
        f"{metadata}"
        "---\n\n# Fixture\n",
    )

    result = _run_make("lint", skill_dir)

    assert result.returncode != 0, result.stdout + result.stderr
    assert case in result.stdout + result.stderr, result.stdout + result.stderr


def test_frontmatter_lint_reports_an_early_failure(tmp_path: Path) -> None:
    """A failure in any skill fails the target, not just one in the final skill.

    The shell `for` loop otherwise exits with the status of its last iteration,
    letting a conformant trailing skill mask a malformed earlier one.
    """
    broken = _write_manifest(tmp_path / "a-broken", "---\nname: [unclosed\n---\n\n# Broken\n")
    valid = _write_manifest(
        tmp_path / "z-valid",
        "---\nname: z-valid\ndescription: A conformant trailing fixture.\n---\n\n# Valid\n",
    )

    result = _run_make("skill-frontmatter-lint", broken, valid)

    assert result.returncode != 0, result.stdout + result.stderr


def test_lint_runs_the_manifest_contract(tmp_path: Path) -> None:
    """`make lint` fails on a malformed manifest, proving the targets are wired in.

    The contract is only enforced because `lint` depends on
    `skill-manifest-check`; without this test, dropping that prerequisite would
    silently disable manifest validation while every other test still passed.
    The fixture is named in the failure output, so a failure raised by the
    Markdown or Mermaid gates cannot pass this test.
    """
    skill_dir = _write_manifest(
        tmp_path / "unlintable",
        "---\ndescription: A fixture that lacks the required discovery name.\n---\n\n# Fixture\n",
    )

    result = _run_make("lint", skill_dir)

    assert result.returncode != 0, result.stdout + result.stderr
    assert "unlintable" in result.stdout + result.stderr, result.stdout + result.stderr


def test_frontmatter_lint_reports_an_unreadable_manifest(tmp_path: Path) -> None:
    """A manifest that cannot be read fails the target rather than being skipped.

    `awk` fails to read a missing `SKILL.md`, a distinct failure path from
    `yamllint` rejecting parsed content, and one that only `pipefail` surfaces.
    """
    absent = tmp_path / "absent"
    absent.mkdir()
    valid = _write_manifest(
        tmp_path / "z-valid",
        "---\nname: z-valid\ndescription: A conformant trailing fixture.\n---\n\n# Valid\n",
    )

    result = _run_make("skill-frontmatter-lint", absent, valid)

    assert result.returncode != 0, result.stdout + result.stderr
