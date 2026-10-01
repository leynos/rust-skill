"""Compile the shipped Polonius control fixtures with their pinned nightly."""

from __future__ import annotations

import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "skills/nll-to-polonius/references/fixtures"
TOOLCHAIN = "nightly-2026-08-27"
CHECKERS = ("off", "next")
SOLVERS = ("no", "globally")
FIXTURE_NAMES = ("case3", "compatible", "alias")


def compiler_command() -> list[str] | None:
    """Return the rustup-proxy command for the pinned compiler.

    Returns
    -------
    list[str] or None
        Executable and toolchain selector when `rustc` is on `PATH`, otherwise
        `None` so the caller can report the missing prerequisite.
    """
    rustc = shutil.which("rustc")
    if rustc is None:
        return None
    return [rustc, f"+{TOOLCHAIN}"]


def expected_diagnostic(fixture: str, checker: str) -> str | None:
    """Return the expected borrow error code for a rejected control.

    Parameters
    ----------
    fixture : str
        Name of a checked-in source file without its `.rs` suffix.
    checker : str
        Checker selection, either `off` or `next`.

    Returns
    -------
    str or None
        Expected diagnostic code for a rejected program, or `None` when the
        fixture should compile successfully.
    """
    if fixture == "case3" and checker == "off":
        return "E0502"
    if fixture == "alias":
        return "E0499"
    return None


def main() -> int:
    """Compile and classify every fixture/checker/solver matrix cell.

    Returns
    -------
    int
        Zero when every observed result matches its expected control outcome;
        nonzero for a missing compiler, identity failure, or mismatched cell.
    """
    command = compiler_command()
    if command is None:
        print(
            "rustc is required to run the Polonius compile-time controls",
            file=sys.stderr,
        )
        return 2

    identity = subprocess.run(
        [*command, "-Vv"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=30,
    )
    if identity.returncode != 0:
        print(
            f"could not obtain identity for {TOOLCHAIN}:\n{identity.stdout}",
            file=sys.stderr,
        )
        return 2

    build_root = ROOT / "target"
    build_root.mkdir(exist_ok=True)
    evidence = Path(tempfile.mkdtemp(prefix="polonius-controls-", dir=build_root))
    compiler_identity = f"toolchain: {TOOLCHAIN}\n{identity.stdout}"
    (evidence / "compiler.txt").write_text(compiler_identity, encoding="utf-8")
    results = ["fixture\tchecker\tsolver\texit\texpected-diagnostic"]
    failures: list[str] = []

    for fixture in FIXTURE_NAMES:
        for checker in CHECKERS:
            for solver in SOLVERS:
                name = f"{fixture}-{checker}-{solver}"
                output = evidence / f"{name}.rmeta"
                args = [
                    *command,
                    "--edition=2024",
                    "--crate-type=lib",
                    "--emit=metadata",
                    f"-Zpolonius={checker}",
                    f"-Znext-solver={solver}",
                    str(FIXTURES / f"{fixture}.rs"),
                    "-o",
                    str(output),
                ]
                (evidence / f"{name}.command").write_text(
                    shlex.join(args) + "\n", encoding="utf-8"
                )
                result = subprocess.run(
                    args,
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=30,
                )
                (evidence / f"{name}.log").write_text(result.stdout, encoding="utf-8")
                diagnostic = expected_diagnostic(fixture, checker)
                expected_status = 0 if diagnostic is None else 1
                results.append(
                    f"{fixture}\t{checker}\t{solver}\t{result.returncode}\t"
                    f"{diagnostic or '-'}"
                )
                accepted = result.returncode == 0
                diagnostic_matches = diagnostic is None or diagnostic in result.stdout
                if accepted != (expected_status == 0) or not diagnostic_matches:
                    failures.append(
                        f"{name}: expected status {expected_status}"
                        f" and diagnostic {diagnostic or 'none'}, got "
                        f"status {result.returncode}; see {name}.log"
                    )

    (evidence / "results.tsv").write_text("\n".join(results) + "\n", encoding="utf-8")
    print("\n".join(results))
    print(f"Evidence directory: {evidence}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        for failure in failures:
            name = failure.split(":", 1)[0]
            log_path = evidence / f"{name}.log"
            print(
                f"\n--- {log_path.name} ---\n{log_path.read_text(encoding='utf-8')}",
                file=sys.stderr,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
