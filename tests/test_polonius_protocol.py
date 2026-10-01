"""Exercise documented shell controls with fake compiler and Cargo commands.

The fake tools record exactly what the examples invoke. The checked-in Rust
fixtures are compiled separately by `tests/polonius_compile_matrix.py`; these
tests cover command construction and Cargo flag precedence. Fake-tool tests
verify command handling only; they do not establish real Rust compiler
acceptance or actual Cargo configuration integration.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import TypedDict

import pytest


PROTOCOL = (
    Path(__file__).resolve().parents[1]
    / "skills/nll-to-polonius/references/verification.md"
)
PIN = "+nightly-2026-08-27"
MARKERS = ("polonius-rustc-matrix", "polonius-cargo-comparison")
BASH = shutil.which("bash")
pytestmark = pytest.mark.skipif(BASH is None, reason="Examples require Bash")


class Invocation(TypedDict):
    """Arguments recorded by a fake compiler or Cargo command."""

    tool: str
    args: list[str]
    encoded: str | None


FAKE_TOOL = r"""
import json
import os
from pathlib import Path
import sys

args = sys.argv[1:]
tool = Path(sys.argv[0]).name
with open(os.environ["INVOCATIONS"], "a", encoding="utf-8") as stream:
    stream.write(json.dumps({
        "tool": tool,
        "args": args,
        "encoded": os.environ.get("CARGO_ENCODED_RUSTFLAGS"),
    }) + "\n")
if "-Vv" in args or "-V" in args:
    print("fake version identity")
    sys.exit(int(os.environ.get("VERSION_EXIT", "0")))
if tool == "rustc":
    fixture = next(Path(arg).stem for arg in args if arg.endswith(".rs"))
    checker = next(arg.split("=", 1)[1] for arg in args
                   if arg.startswith("-Zpolonius="))
    solver = next(arg.split("=", 1)[1] for arg in args
                  if arg.startswith("-Znext-solver="))
    status = 1 if fixture == "alias" or (fixture == "case3" and checker == "off") else 0
    if os.environ.get("INFRA_FAILURE") and (fixture, checker, solver) == (
        "compatible", "next", "globally"
    ):
        status = 42
else:
    flags = os.environ["CARGO_ENCODED_RUSTFLAGS"].split("\x1f")
    status = 101 if "-Zpolonius=off" in flags else 0
print("first diagnostic line", file=sys.stderr)
print("middle diagnostic line", file=sys.stderr)
print("last diagnostic line", file=sys.stderr)
sys.exit(status)
"""


def command(marker: str) -> str:
    """Extract one documented Bash example from the verification reference.

    Parameters
    ----------
    marker : str
        HTML marker immediately before the command's fenced code block.

    Returns
    -------
    str
        The complete Bash program, terminated by a newline.

    Raises
    ------
    AssertionError
        If the reference does not contain exactly one matching command.
    """
    pattern = rf"<!-- {re.escape(marker)} -->\s*```bash\n(.*?)\n```"
    matches: list[str] = re.findall(pattern, PROTOCOL.read_text(encoding="utf-8"), re.S)
    assert len(matches) == 1, f"Expected one documented command for {marker}"
    return matches[0] + "\n"


@pytest.fixture
def tool_environment(tmp_path: Path) -> dict[str, str]:
    """Build fake compiler commands and an isolated environment for examples.

    Parameters
    ----------
    tmp_path : Path
        Pytest's temporary directory for this test.

    Returns
    -------
    dict[str, str]
        Environment variables directing command lookups, evidence files, and
        fake-tool behaviour into the temporary directory.
    """
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for tool in ("rustc", "cargo"):
        executable = bindir / tool
        executable.write_text(f"#!/usr/bin/env python3\n{FAKE_TOOL}", encoding="utf-8")
        executable.chmod(0o755)
    fixtures = tmp_path / "fixtures"
    shutil.copytree(PROTOCOL.parent / "fixtures", fixtures)
    evidence = tmp_path / "evidence with spaces"
    evidence.mkdir()
    return {
        **os.environ,
        "PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}",
        "TMPDIR": str(evidence),
        "POLONIUS_FIXTURES": str(fixtures),
        "INVOCATIONS": str(tmp_path / "invocations.jsonl"),
        # Deliberately contaminate both sources. The Cargo example must replace
        # the higher-precedence one rather than merely appending to RUSTFLAGS.
        "CARGO_ENCODED_RUSTFLAGS": "-Zpolonius=next\x1f-Znext-solver=globally",
        "RUSTFLAGS": "-Zpolonius=next -Znext-solver=globally",
        "VERSION_EXIT": "0",
        "INFRA_FAILURE": "",
    }


def execute(
    script: str, env: dict[str, str], cwd: Path
) -> subprocess.CompletedProcess[str]:
    """Run a documented Bash program in a bounded subprocess.

    Parameters
    ----------
    script : str
        Complete Bash source to execute.
    env : dict[str, str]
        Environment passed to the child process, including the fake tools.
    cwd : Path
        Working directory used by the child process.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Completed process details with captured text output and its raw status.
    """
    assert BASH is not None, "Bash is required to execute the documented examples"
    return subprocess.run(
        [BASH, "-c", script],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )


def invocations(env: dict[str, str]) -> list[Invocation]:
    """Read and decode the fake tools' newline-delimited invocation log.

    Parameters
    ----------
    env : dict[str, str]
        Environment containing the `INVOCATIONS` path used by fake tools.

    Returns
    -------
    list[Invocation]
        One JSON object per invocation, including the tool name, arguments,
        and effective encoded Cargo flags.
    """
    return [
        json.loads(line)
        for line in Path(env["INVOCATIONS"]).read_text(encoding="utf-8").splitlines()
    ]


def evidence_directory(result: subprocess.CompletedProcess[str]) -> Path:
    """Return the evidence directory printed by a successful example.

    Parameters
    ----------
    result : subprocess.CompletedProcess[str]
        Captured process result from a documented comparison command.

    Returns
    -------
    Path
        Directory named by the unique `Evidence directory:` output line.

    Raises
    ------
    AssertionError
        If the command failed or did not print exactly one evidence path.
    """
    assert result.returncode == 0, f"Documented command failed: {result.stderr}"
    prefix = "Evidence directory: "
    paths = [
        line.removeprefix(prefix)
        for line in result.stdout.splitlines()
        if line.startswith(prefix)
    ]
    assert len(paths) == 1, (
        f"Expected one evidence directory in output: {result.stdout}"
    )
    return Path(paths[0])


@pytest.mark.parametrize("marker", MARKERS)
def test_documented_commands_have_valid_bash_syntax(marker: str) -> None:
    """Check that each documented command parses in Bash syntax-only mode."""
    assert BASH is not None, "Bash is required to check the documented command syntax"
    result = subprocess.run(
        [BASH, "-n"],
        input=command(marker),
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, (
        f"documented Rust matrix command failed: {result.stderr}"
    )


def test_rustc_matrix_keeps_all_cells_and_diagnostics(
    tmp_path: Path,
    tool_environment: dict[str, str],
) -> None:
    """Verify the fake rustc command records all matrix cells and evidence.

    This checks command handling and retained diagnostics, not real Rust
    compiler acceptance.
    """
    result = execute(command(MARKERS[0]), tool_environment, tmp_path)
    out = evidence_directory(result)
    calls = invocations(tool_environment)
    assert calls[0]["args"] == [PIN, "-Vv"], (
        "the first matrix call must record compiler identity"
    )
    assert len(calls) == 13, (
        "the matrix must record identity plus all twelve fixture cells"
    )
    observed = set()
    for call in calls[1:]:
        args = call["args"]
        assert args[0] == PIN, (
            f"rustc invocation omitted pinned toolchain {PIN}: {args!r}"
        )
        assert "--edition=2024" in args, (
            f"rustc invocation omitted edition argument: {args!r}"
        )
        assert "--emit=metadata" in args, (
            f"rustc invocation omitted metadata output: {args!r}"
        )
        checkers = [arg for arg in args if arg.startswith("-Zpolonius=")]
        solvers = [arg for arg in args if arg.startswith("-Znext-solver=")]
        assert len(checkers) == 1, (
            f"rustc invocation must select exactly one checker: {args!r}"
        )
        assert len(solvers) == 1, (
            f"rustc invocation must select exactly one solver: {args!r}"
        )
        fixture = next(Path(arg).stem for arg in args if arg.endswith(".rs"))
        observed.add((fixture, checkers[0], solvers[0]))
    expected_cells = {
        (fixture, f"-Zpolonius={checker}", f"-Znext-solver={solver}")
        for fixture in ("case3", "compatible", "alias")
        for checker in ("off", "next")
        for solver in ("no", "globally")
    }
    assert observed == expected_cells, (
        "the documented matrix omitted or duplicated fixture cells"
    )
    rows = (out / "results.tsv").read_text().splitlines()
    assert rows[0] == "fixture\tchecker\tsolver\texit", (
        "the results table has the wrong header"
    )
    assert len(rows) == 13, "the results table must contain its header and twelve cells"
    for fixture in ("case3", "compatible", "alias"):
        for checker in ("off", "next"):
            for solver in ("no", "globally"):
                expected = int(
                    fixture == "alias" or (fixture == "case3" and checker == "off")
                )
                assert f"{fixture}\t{checker}\t{solver}\t{expected}" in rows, (
                    f"missing expected status for {fixture}/{checker}/{solver}: {rows!r}"
                )
                name = f"{fixture}-{checker}-{solver}"
                assert (out / f"{name}.log").read_text().splitlines() == [
                    "first diagnostic line",
                    "middle diagnostic line",
                    "last diagnostic line",
                ], f"the complete diagnostic log was not retained for {name}"
                assert (
                    f"-Zpolonius={checker}" in (out / f"{name}.command").read_text()
                ), f"the archived command omitted checker {checker} for {name}"
    assert (out / "compiler.txt").read_text().strip() == "fake version identity", (
        "the matrix did not preserve compiler identity"
    )


def test_matrix_retains_unexpected_failure_without_stopping(
    tmp_path: Path,
    tool_environment: dict[str, str],
) -> None:
    """Check that a fake rustc failure is recorded while later cells run.

    This verifies command failure handling, not real Rust compiler acceptance.
    """
    tool_environment["INFRA_FAILURE"] = "1"
    out = evidence_directory(execute(command(MARKERS[0]), tool_environment, tmp_path))
    rows = (out / "results.tsv").read_text().splitlines()
    assert "compatible\tnext\tglobally\t42" in rows, (
        "the unexpected status 42 was not retained"
    )
    assert rows[-1] == "alias\tnext\tglobally\t1", (
        "execution stopped before the final matrix cell"
    )
    assert len(invocations(tool_environment)) == 13, (
        "unexpected failure stopped later compiler calls"
    )


@pytest.mark.parametrize("common", [(), ("--cfg", 'feature="boundary test"')])
def test_cargo_comparison_replaces_encoded_flags_and_isolates_outputs(
    tmp_path: Path,
    tool_environment: dict[str, str],
    common: tuple[str, ...],
) -> None:
    """Verify the fake Cargo command replaces flags and separates build output.

    The fake tool checks command handling and evidence retention, not actual
    Cargo configuration integration or Rust compiler acceptance.
    """
    script = command(MARKERS[1])
    if common:
        script = script.replace(
            "common=()", "common=(--cfg 'feature=\"boundary test\"')"
        )
    out = evidence_directory(execute(script, tool_environment, tmp_path))
    calls = invocations(tool_environment)
    assert calls[0]["args"] == [PIN, "-Vv"], (
        "Cargo comparison must record rustc identity first"
    )
    assert calls[1]["args"] == [PIN, "-V"], (
        "Cargo comparison must record Cargo identity second"
    )
    assert len(calls) == 4, (
        "Cargo comparison must record two identities and two checker builds"
    )
    for call, checker in zip(calls[2:], ("off", "next"), strict=True):
        assert call["tool"] == "cargo", (
            f"comparison invocation used the wrong tool: {call!r}"
        )
        encoded_flags = call["encoded"]
        assert encoded_flags is not None, (
            f"Cargo invocation omitted encoded flags: {call!r}"
        )
        assert encoded_flags.split("\x1f") == [
            *common,
            f"-Zpolonius={checker}",
            "-Znext-solver=no",
        ], f"Cargo flags did not isolate checker {checker}: {call!r}"
        assert call["args"] == [
            PIN,
            "check",
            "--locked",
            "--all-targets",
            "-vv",
            "--target-dir",
            str(out / f"target-{checker}"),
        ], f"Cargo build arguments did not isolate output for {checker}: {call!r}"
        assert (out / f"{checker}.log").read_text().splitlines() == [
            "first diagnostic line",
            "middle diagnostic line",
            "last diagnostic line",
        ], f"the complete Cargo diagnostic log was not retained for {checker}"
    assert (out / "results.tsv").read_text().splitlines() == [
        "checker\texit",
        "off\t101",
        "next\t0",
    ], "Cargo checker statuses were not recorded as expected"
    assert (out / "cargo.txt").read_text().strip() == "fake version identity", (
        "the Cargo comparison did not preserve compiler identity"
    )


@pytest.mark.parametrize("marker", MARKERS)
def test_missing_compiler_identity_aborts_before_comparison(
    tmp_path: Path,
    tool_environment: dict[str, str],
    marker: str,
) -> None:
    """Check that failed fake compiler identity prevents comparison commands.

    This verifies command failure handling, not real Rust compiler acceptance.
    """
    tool_environment["VERSION_EXIT"] = "23"
    result = execute(command(marker), tool_environment, tmp_path)
    assert result.returncode == 23, "compiler identity failure was not propagated"
    assert "Evidence directory:" not in result.stdout, (
        "comparison ran without compiler identity"
    )
    assert len(invocations(tool_environment)) == 1, (
        "comparison continued after compiler identity failed"
    )
