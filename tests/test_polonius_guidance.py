"""Contract tests for the shipped Polonius Alpha guidance.

The catalogue is prose: this repository ships no Rust source, no Cargo
manifest, and no executable router. A skill's "behaviour" is therefore
instructions a model reads, and the honest contract to pin is the *textual*
one — the vocabulary, the command shapes, and the routing distinctions that
must not silently disappear, invert, or drift.

Each test below guards a claim the guidance turns on. They are written to fail
loudly if someone deletes the claim, inverts it, or replaces it with a
plausible-looking constant, because those are the edits that would leave every
other gate green while the advice quietly became wrong.

**What these tests cannot do.** They validate the catalogue's text, not
compiler semantics. They cannot prove that `-Zpolonius=off` really forces NLL,
that the canary really discriminates Alpha from NLL, or that the recorded Cargo
flag-precedence behaviour is correct. Those were verified by hand against a
real Cargo project on a nightly toolchain, are reproducible, and are *not*
enforced by any gate — see
`docs/verification-review-failure-modes.md` for the estate's posture on
hand-verification. A future edit can invalidate the advice without failing
anything here.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS = REPO_ROOT / "skills"

POSTURE_REFERENCE = SKILLS / "rust-router" / "references" / "polonius-alpha.md"
ROUTING_MATRIX = SKILLS / "rust-router" / "references" / "routing-matrix.md"
MIGRATION_SKILL = SKILLS / "nll-to-polonius" / "SKILL.md"
USERS_GUIDE = REPO_ROOT / "docs" / "users-guide.md"

# The four values the router records as ambient borrow-checker posture. A
# missing or renamed value silently changes the vocabulary every downstream
# skill is told to reason with.
POSTURE_VALUES = ("nll", "polonius-alpha", "polonius-legacy", "unknown")

# Explicit checker selection, as documented. The mapping is the whole basis of
# posture detection, so each pairing is asserted separately rather than as one
# blob: inverting a single pairing is exactly the regression to catch.
CHECKER_SELECTION = {
    "next": "polonius-alpha",
    "off": "nll",
    "legacy": "polonius-legacy",
}

# The routing boundary. Borrow-checker *errors* stay with the ordinary
# ownership skill; Polonius *adoption and migration* is the only work that
# routes to the migration skill.
BORROW_ERROR_CODES = ("E0382", "E0502", "E0597")
ORDINARY_OWNERSHIP_SKILL = "rust-memory-and-state"
MIGRATION_SKILL_NAME = "nll-to-polonius"

# Skills that consume the posture rather than duplicating a Polonius edition.
POSTURE_CONSUMERS = (
    "rust-memory-and-state",
    "rust-async-and-concurrency",
    "rust-performance-and-layout",
)

# A `cargo rustc` invocation that hard-codes a library target. Cargo compiles
# only the named target, so a hard-coded `--lib` misses the borrow-sensitive
# code in a binary or example package and fails outright in a package with no
# library target. Either way the control is silently skipped, so no control
# command in the migration tree may name a fixed library target.
HARD_CODED_LIB_CONTROL = re.compile(r"cargo rustc --lib\b")

# The migration skill's compiler controls live in its verification protocol,
# which selects the control through the highest-precedence rustflags source
# rather than a trailing `cargo rustc` argument.
VERIFICATION_PROTOCOL = SKILLS / "nll-to-polonius" / "references" / "verification.md"


def _read(path: Path) -> str:
    """Read a shipped document, naming it in any locale-independent failure."""
    assert path.is_file(), f"expected {path} to exist"
    return path.read_text(encoding="utf-8")


def _bullet_lines(text: str) -> list[str]:
    """Return the stripped text of list items, for structure-aware matching.

    Asserting over bullets rather than the whole document keeps a reworded
    paragraph from breaking an unrelated test.
    """
    return [
        stripped
        for line in text.splitlines()
        if (stripped := line.strip()).startswith(("- ", "* ", "1. "))
    ]


def test_posture_vocabulary_is_complete() -> None:
    """The reference names all four posture values.

    Downstream skills are told to branch on these exact strings; dropping one
    leaves a documented posture that no skill can name.
    """
    text = _read(POSTURE_REFERENCE)
    missing = [value for value in POSTURE_VALUES if value not in text]
    assert not missing, f"posture reference is missing {missing}"


def test_explicit_checker_selection_maps_each_flag_to_a_posture() -> None:
    """Each `-Zpolonius` spelling maps to its documented posture.

    Asserted per pairing, on the bullet that carries it, so inverting a single
    mapping fails here rather than passing on the other two.
    """
    bullets = _bullet_lines(_read(POSTURE_REFERENCE))
    for flag, posture in CHECKER_SELECTION.items():
        selector = f"-Zpolonius={flag}"
        matched = [
            bullet for bullet in bullets if selector in bullet and posture in bullet
        ]
        assert matched, f"no bullet maps {selector} to {posture}"


def test_current_nightly_defaults_to_alpha() -> None:
    """Current nightly enables Alpha, so omitting `next` is not an NLL control.

    This is the claim the August 2026 refresh turns on, and the one most
    likely to be silently reverted to the older "pass `-Zpolonius=next` to get
    Alpha" wording.
    """
    text = _read(POSTURE_REFERENCE)
    assert "current Rust nightly enables Polonius Alpha by default" in text, (
        "the reference no longer states the current-nightly Alpha default"
    )
    assert "-Zpolonius=off" in text and "-Zpolonius=next" in text, (
        "the reference no longer names both explicit checker selections"
    )


def test_migration_skill_defers_to_the_shared_posture_reference() -> None:
    """The migration skill consumes the posture reference rather than restating it.

    The scope split: the router owns posture detection and the canary, the
    migration skill owns compiler controls and attribution. If the cross-link
    is dropped, the migration skill loses the canary and the posture
    vocabulary, and the two documents drift apart.
    """
    skill = _read(MIGRATION_SKILL)
    assert "polonius-alpha.md" in skill, (
        "the migration skill no longer links the shared posture reference"
    )
    assert "canary" in skill, (
        "the migration skill no longer points at the compile canary"
    )

    protocol = _read(VERIFICATION_PROTOCOL)
    assert "CARGO_ENCODED_RUSTFLAGS" in protocol, (
        "the verification protocol no longer selects the control through "
        "encoded rustflags"
    )


def test_canary_is_a_runnable_target_that_discriminates() -> None:
    """The canary keeps its discriminating shape and its entry point.

    Three separate facts, each of which has already been got wrong once: the
    reborrow shape must be the NLL-rejected one, the example must have a
    `main` (without it the example fails before borrow checking and proves
    nothing), and the reference must state which posture accepts it.
    """
    text = _read(POSTURE_REFERENCE)

    assert "fn reborrow(a: &mut u8) -> &mut u8" in text, (
        "the canary no longer defines the reborrow function"
    )
    assert "let b = &mut *a;" in text and "if true { b } else { a }" in text, (
        "the canary no longer has the conditional-return body that NLL rejects"
    )
    assert "fn main()" in text, (
        "the canary example has no `main`, so it would fail on its missing "
        "entry point before borrow checking runs"
    )
    assert "accepted by Polonius Alpha and rejected by NLL" in text, (
        "the reference no longer states that the canary discriminates"
    )
    assert "Keep the `main` function" in text, (
        "the reference no longer explains why `main` is required"
    )


def test_no_control_command_hard_codes_a_library_target() -> None:
    """No control command may hard-code `--lib`.

    Cargo compiles only the named target, so a hard-coded `--lib` misses the
    changed code in a binary or example package and fails outright in a
    package with no library target. Either outcome silently skips the control —
    the migration skill's central discriminator. The guard covers the whole
    migration tree, so it still holds if a `cargo rustc` control is ever
    reintroduced beside the encoded-flags protocol.
    """
    migration = SKILLS / "nll-to-polonius"
    offending = [
        f"{path.relative_to(REPO_ROOT)}:{line_no}"
        for path in sorted(migration.rglob("*.md"))
        for line_no, line in enumerate(_read(path).splitlines(), start=1)
        if HARD_CODED_LIB_CONTROL.search(line)
    ]
    assert not offending, "a control command hard-codes a library target: " + ", ".join(
        offending
    )

    protocol = _read(VERIFICATION_PROTOCOL)
    assert "--all-targets" in protocol, (
        "the verification protocol no longer builds every target in the "
        "comparison, so a borrow-sensitive example or binary would be skipped"
    )


def test_configuration_override_targets_the_projects_own_key() -> None:
    """The override names the key that supplies the project's flag.

    A `--config` override of `build.rustflags` is ignored outright once a
    target-scoped `rustflags` key exists, so the control never reaches rustc.
    The reference must therefore document the target-scoped form — and must
    not present the broken one as the remedy.
    """
    text = _read(POSTURE_REFERENCE)

    assert 'target."cfg(all())".rustflags' in text, (
        "the reference no longer documents the target-scoped override"
    )
    assert "same key that supplies the project's flag" in text, (
        "the reference no longer states the key-matching rule"
    )

    # `build.rustflags` may survive only as the defect being corrected. It must
    # not appear inside a recommended `--config` command.
    recommended = re.findall(r"--config\s+'([^']*build\.rustflags[^']*)'", text)
    assert not recommended, (
        f"the reference recommends a build.rustflags override: {recommended}"
    )


def test_trailing_argument_masking_is_explained_by_last_occurrence() -> None:
    """The trailing-flag case keeps its own, different explanation.

    Two distinct mechanisms are documented here, and conflating them is the
    specific error the reference was corrected for: a trailing argument is
    masked by last-occurrence, while a mis-keyed configuration override is
    ignored by key precedence.
    """
    text = _read(POSTURE_REFERENCE)
    assert "honours the last occurrence" in text, (
        "the reference no longer explains last-occurrence masking"
    )
    assert "key precedence, not last-occurrence" in text, (
        "the reference no longer distinguishes key precedence from "
        "last-occurrence masking"
    )


def test_posture_is_ambient_context_rather_than_a_route() -> None:
    """Posture informs routing; it is not itself a destination.

    This is the architectural claim of the change. If it regresses, every
    Alpha project starts routing to the migration skill instead of the
    ordinary language skill that owns the concrete problem.
    """
    matrix = _read(ROUTING_MATRIX)
    assert "ambient context, not a route of its own" in matrix, (
        "the routing matrix no longer states that posture is ambient context"
    )
    assert "adoption, audits, and migration work" in matrix, (
        "the routing matrix no longer scopes the migration skill"
    )

    for code in BORROW_ERROR_CODES:
        assert code in matrix, f"the routing matrix no longer routes {code} by its code"
    assert ORDINARY_OWNERSHIP_SKILL in matrix, (
        "the routing matrix no longer routes ordinary borrow failures to "
        f"{ORDINARY_OWNERSHIP_SKILL}"
    )
    assert MIGRATION_SKILL_NAME in matrix, (
        "the routing matrix no longer names the migration skill"
    )


def test_alpha_does_not_claim_to_remove_permanent_constraints() -> None:
    """The boundary that stops the guidance overclaiming.

    Alpha relaxes lifetime reasoning, not aliasing or ownership across
    concurrency boundaries. Losing this section would invite a model to read
    Alpha as licensing borrows it does not make sound.
    """
    text = _read(POSTURE_REFERENCE)
    assert "does not relax mutation-xor-sharing" in text, (
        "the reference no longer states that Alpha does not relax aliasing"
    )
    assert "`Send` and `Sync` requirements" in text, (
        "the reference no longer lists `Send`/`Sync` as unchanged"
    )
    assert "suspension-point, task, and thread ownership" in text, (
        "the reference no longer keeps ownership across suspension points"
    )


def test_posture_reaches_the_ordinary_skills() -> None:
    """The three named ordinary skills consume the posture.

    The reference's whole purpose is to be read by the skills doing ordinary
    work; if the consumer list is dropped, the posture has no documented
    audience.
    """
    text = _read(POSTURE_REFERENCE)
    for skill in POSTURE_CONSUMERS:
        assert skill in text, f"the reference no longer names {skill}"


def test_users_guide_documents_the_posture_and_its_control() -> None:
    """The user-facing guide carries the posture values and the canary.

    Contributors and users read the guide, not the router's references, so the
    vocabulary must be reachable from the user-facing entry point.
    """
    text = _read(USERS_GUIDE)
    for value in POSTURE_VALUES:
        assert value in text, f"the users' guide no longer documents {value}"
    assert "canary" in text, "the users' guide no longer mentions the compile canary"
