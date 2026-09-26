"""Exercise the documented shell controls, not Rust compiler acceptance.

The fake tools record exactly what the examples invoke. Real compiler probes,
Cargo configuration integration, and repository support gates remain separate.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest


PROTOCOL = (
    Path(__file__).resolve().parents[1]
    / "skills/nll-to-polonius/references/verification.md"
)
PIN = "+nightly-2026-08-27"
MARKERS = ("polonius-rustc-matrix", "polonius-cargo-comparison")
BASH = shutil.which("bash")
pytestmark = pytest.mark.skipif(BASH is None, reason="Examples require Bash")


FAKE_TOOL = r'''
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
'''


def command(marker: str) -> str:
    """Read the shipped example rather than maintaining a second copy."""
    pattern = rf"<!-- {re.escape(marker)} -->\s*```bash\n(.*?)\n```"
    matches = re.findall(pattern, PROTOCOL.read_text(encoding="utf-8"), re.S)
    assert len(matches) == 1, f"Expected one documented command for {marker}"
    return matches[0] + "\n"


@pytest.fixture
def tool_environment(tmp_path: Path) -> dict[str, str]:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for tool in ("rustc", "cargo"):
        executable = bindir / tool
        executable.write_text(f"#!{sys.executable}\n{FAKE_TOOL}", encoding="utf-8")
        executable.chmod(0o755)
    evidence = tmp_path / "evidence with spaces"
    evidence.mkdir()
    return {
        **os.environ,
        "PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}",
        "TMPDIR": str(evidence),
        "INVOCATIONS": str(tmp_path / "invocations.jsonl"),
        # Deliberately contaminate both sources. The Cargo example must replace
        # the higher-precedence one rather than merely appending to RUSTFLAGS.
        "CARGO_ENCODED_RUSTFLAGS": "-Zpolonius=next\x1f-Znext-solver=globally",
        "RUSTFLAGS": "-Zpolonius=next -Znext-solver=globally",
        "VERSION_EXIT": "0",
        "INFRA_FAILURE": "",
    }


def execute(script: str, env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    assert BASH is not None
    return subprocess.run(
        [BASH, "-c", script], cwd=cwd, env=env, text=True,
        capture_output=True, timeout=20, check=False,
    )


def invocations(env: dict[str, str]) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in Path(env["INVOCATIONS"]).read_text(encoding="utf-8").splitlines()
    ]


def evidence_directory(result: subprocess.CompletedProcess[str]) -> Path:
    assert result.returncode == 0, result.stderr
    prefix = "Evidence directory: "
    paths = [line.removeprefix(prefix) for line in result.stdout.splitlines()
             if line.startswith(prefix)]
    assert len(paths) == 1, result.stdout
    return Path(paths[0])


@pytest.mark.parametrize("marker", MARKERS)
def test_documented_commands_have_valid_bash_syntax(marker: str) -> None:
    assert BASH is not None
    result = subprocess.run(
        [BASH, "-n"], input=command(marker), text=True, capture_output=True,
        timeout=10, check=False,
    )
    assert result.returncode == 0, result.stderr


def test_rustc_matrix_keeps_all_cells_and_diagnostics(
    tmp_path: Path, tool_environment: dict[str, str],
) -> None:
    result = execute(command(MARKERS[0]), tool_environment, tmp_path)
    out = evidence_directory(result)
    calls = invocations(tool_environment)
    assert calls[0]["args"] == [PIN, "-Vv"]
    assert len(calls) == 13
    observed = set()
    for call in calls[1:]:
        args = call["args"]
        assert args[0] == PIN
        assert "--edition=2024" in args and "--emit=metadata" in args
        checkers = [arg for arg in args if arg.startswith("-Zpolonius=")]
        solvers = [arg for arg in args if arg.startswith("-Znext-solver=")]
        assert len(checkers) == len(solvers) == 1
        fixture = next(Path(arg).stem for arg in args if arg.endswith(".rs"))
        observed.add((fixture, checkers[0], solvers[0]))
    assert observed == {
        (fixture, f"-Zpolonius={checker}", f"-Znext-solver={solver}")
        for fixture in ("case3", "compatible", "alias")
        for checker in ("off", "next") for solver in ("no", "globally")
    }
    rows = (out / "results.tsv").read_text().splitlines()
    assert rows[0] == "fixture\tchecker\tsolver\texit"
    assert len(rows) == 13
    for fixture in ("case3", "compatible", "alias"):
        for checker in ("off", "next"):
            for solver in ("no", "globally"):
                expected = int(fixture == "alias" or (fixture == "case3" and checker == "off"))
                assert f"{fixture}\t{checker}\t{solver}\t{expected}" in rows
                name = f"{fixture}-{checker}-{solver}"
                assert (out / f"{name}.log").read_text().splitlines() == [
                    "first diagnostic line", "middle diagnostic line", "last diagnostic line",
                ]
                assert f"-Zpolonius={checker}" in (out / f"{name}.command").read_text()
    assert (out / "compiler.txt").read_text().strip() == "fake version identity"


def test_matrix_retains_unexpected_failure_without_stopping(
    tmp_path: Path, tool_environment: dict[str, str],
) -> None:
    tool_environment["INFRA_FAILURE"] = "1"
    out = evidence_directory(execute(command(MARKERS[0]), tool_environment, tmp_path))
    rows = (out / "results.tsv").read_text().splitlines()
    assert "compatible\tnext\tglobally\t42" in rows
    assert rows[-1] == "alias\tnext\tglobally\t1"
    assert len(invocations(tool_environment)) == 13


@pytest.mark.parametrize("common", [(), ("--cfg", 'feature="boundary test"')])
def test_cargo_comparison_replaces_encoded_flags_and_isolates_outputs(
    tmp_path: Path, tool_environment: dict[str, str], common: tuple[str, ...],
) -> None:
    script = command(MARKERS[1])
    if common:
        script = script.replace("common=()", "common=(--cfg 'feature=\"boundary test\"')")
    out = evidence_directory(execute(script, tool_environment, tmp_path))
    calls = invocations(tool_environment)
    assert calls[0]["args"] == [PIN, "-Vv"]
    assert calls[1]["args"] == [PIN, "-V"]
    assert len(calls) == 4
    for call, checker in zip(calls[2:], ("off", "next"), strict=True):
        assert call["tool"] == "cargo"
        assert call["encoded"].split("\x1f") == [
            *common, f"-Zpolonius={checker}", "-Znext-solver=no",
        ]
        assert call["args"] == [
            PIN, "check", "--locked", "--all-targets", "-vv",
            "--target-dir", str(out / f"target-{checker}"),
        ]
        assert (out / f"{checker}.log").read_text().splitlines() == [
            "first diagnostic line", "middle diagnostic line", "last diagnostic line",
        ]
    assert (out / "results.tsv").read_text().splitlines() == [
        "checker\texit", "off\t101", "next\t0",
    ]
    assert (out / "cargo.txt").read_text().strip() == "fake version identity"


@pytest.mark.parametrize("marker", MARKERS)
def test_missing_compiler_identity_aborts_before_comparison(
    tmp_path: Path, tool_environment: dict[str, str], marker: str,
) -> None:
    tool_environment["VERSION_EXIT"] = "23"
    result = execute(command(marker), tool_environment, tmp_path)
    assert result.returncode == 23
    assert "Evidence directory:" not in result.stdout
    assert len(invocations(tool_environment)) == 1
