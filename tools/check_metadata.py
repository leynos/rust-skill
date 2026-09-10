#!/usr/bin/env python3
"""Reject skill manifests whose `metadata` is not a mapping of strings to strings.

`skills-ref` rewrites every metadata entry with `str(v)` instead of rejecting
the shapes the Agent Skills schema forbids, so a YAML sequence or mapping
survives schema validation and reaches consumers as a Python repr. This check
runs ahead of validation, so the `dict[str, str]` contract fails the gate
rather than shipping a silently mangled value.

Each argument is a skill directory or a `SKILL.md` path. The exit status is
non-zero if any manifest breaks the contract.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

FRONTMATTER_FENCE = "---"


def _frontmatter(manifest: Path) -> object:
    """Return the parsed YAML frontmatter of a skill manifest."""
    lines = manifest.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != FRONTMATTER_FENCE:
        raise ValueError("does not open with a frontmatter fence")
    try:
        closing = lines.index(FRONTMATTER_FENCE, 1)
    except ValueError:
        raise ValueError("frontmatter is not closed by a --- fence") from None
    return yaml.safe_load("\n".join(lines[1:closing]))


def _problems(manifest: Path) -> list[str]:
    """List every way the manifest breaks the metadata string contract."""
    try:
        frontmatter = _frontmatter(manifest)
    except (OSError, ValueError, yaml.YAMLError) as problem:
        return [f"cannot read frontmatter: {problem}"]

    if not isinstance(frontmatter, dict):
        return [f"frontmatter must be a mapping, got {type(frontmatter).__name__}"]
    if "metadata" not in frontmatter:
        return []

    metadata = frontmatter["metadata"]
    if not isinstance(metadata, dict):
        return [f"metadata must be a mapping, got {type(metadata).__name__}"]

    problems: list[str] = []
    for key, value in metadata.items():
        if not isinstance(key, str):
            problems.append(f"metadata key {key!r} must be a string")
        if not isinstance(value, str):
            problems.append(
                f"metadata value for {key!r} must be a string, got {type(value).__name__}"
            )
    return problems


def _manifest_path(argument: str) -> Path:
    """Resolve a skill directory or manifest path to its `SKILL.md`."""
    path = Path(argument)
    return path / "SKILL.md" if path.is_dir() else path


def main(arguments: list[str]) -> int:
    """Report every non-conformant manifest, failing if any is found."""
    if not arguments:
        print("usage: check_metadata.py <skill directory or SKILL.md>...", file=sys.stderr)
        return 2

    failed = False
    for argument in arguments:
        manifest = _manifest_path(argument)
        problems = _problems(manifest)
        if not problems:
            print(f"metadata ok: {manifest}")
            continue
        failed = True
        for problem in problems:
            print(f"{manifest}: {problem}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
