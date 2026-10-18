"""Check repository syntax, documentation links and optional source preservation."""

from __future__ import annotations

import argparse
import ast
import hashlib
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "smart_building_conformal"
SOURCE = PACKAGE / "src"
DOCUMENTS = (
    ROOT / "README.md",
    PACKAGE / "README.md",
    ROOT / "docs" / "development.md",
    ROOT / "docs" / "reproducibility.md",
    ROOT / "docs" / "history.md",
)
SMOKE_TESTS = (
    "tests/test_metrics.py",
    "tests/test_no_leakage.py",
    "tests/test_alerts.py",
    "tests/test_windowing_integrity.py",
    "tests/test_statistics.py",
    "tests/test_residual_delay.py",
    "tests/test_extension_statistics.py",
    "tests/test_final_figures.py",
)


def git_output(*arguments: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), *arguments])


def tracked_paths() -> set[str]:
    """Include tracked evidence without downloading a sparse checkout's outputs."""
    if not (ROOT / ".git").exists():
        return set()
    tracked = set(git_output("ls-files", "-z").decode("utf-8").split("\0")) - {""}
    deleted = set(git_output("ls-files", "--deleted", "-z").decode("utf-8").split("\0"))
    return tracked - deleted


def check_syntax() -> tuple[int, list[str]]:
    roots = (
        SOURCE,
        PACKAGE / "scripts",
        PACKAGE / "tests",
        ROOT / "review",
        ROOT / "report_figures",
        ROOT / "tools",
    )
    files = sorted({path for root in roots for path in root.rglob("*.py")})
    errors = []
    for path in files:
        try:
            ast.parse(path.read_bytes(), filename=str(path))
        except SyntaxError as error:
            errors.append(f"{path.relative_to(ROOT)}:{error.lineno}: {error.msg}")
    return len(files), errors


def check_links() -> tuple[int, list[str]]:
    tracked = tracked_paths()
    errors = []
    count = 0
    for document in DOCUMENTS:
        if not document.is_file():
            errors.append(f"Missing documentation: {document.relative_to(ROOT)}")
            continue
        for match in re.finditer(r"!?\[[^\]]*\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            target = match.group(1).strip("<>")
            parts = urlsplit(target)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            resolved = (document.parent / unquote(parts.path)).resolve()
            if not resolved.is_relative_to(ROOT):
                errors.append(f"{document.relative_to(ROOT)}: link leaves the repository: {target}")
                continue
            relative = resolved.relative_to(ROOT).as_posix()
            exists_in_git = relative in tracked or any(
                name.startswith(relative.rstrip("/") + "/") for name in tracked
            )
            if not resolved.exists() and not exists_in_git:
                errors.append(f"{document.relative_to(ROOT)}: missing link target: {target}")
            count += 1
    return count, errors


def check_source(reference: str) -> tuple[int, list[str]]:
    """Compare raw source bytes against an existing commit without importing code."""
    commit = (
        git_output("rev-parse", "--verify", "--end-of-options", reference + "^{commit}")
        .decode()
        .strip()
    )
    entries = git_output("ls-tree", "-r", "-z", commit, "--", SOURCE.relative_to(ROOT).as_posix())
    errors = []
    expected = set()
    for entry in entries.split(b"\0"):
        if not entry:
            continue
        metadata, name = entry.split(b"\t", 1)
        _, kind, expected_hash = metadata.decode().split()
        relative = name.decode("utf-8")
        if kind != "blob" or not relative.endswith(".py"):
            continue
        expected.add(relative)
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"Missing scientific source: {relative}")
            continue
        data = path.read_bytes()
        header = f"blob {len(data)}\0".encode()
        actual_hash = hashlib.sha1(header + data).hexdigest()
        if actual_hash != expected_hash:
            errors.append(f"Scientific source differs from {commit[:12]}: {relative}")
    current = {path.relative_to(ROOT).as_posix() for path in SOURCE.rglob("*.py")}
    errors.extend(f"New scientific source: {name}" for name in sorted(current - expected))
    return len(expected), errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tests", action="store_true", help="also run synthetic, data-free smoke tests"
    )
    parser.add_argument(
        "--source-ref", help="also require byte-identical scientific source to this Git ref"
    )
    args = parser.parse_args()

    errors = []
    for label, check in (
        ("Python files parsed", check_syntax),
        ("Local documentation links", check_links),
    ):
        count, failures = check()
        print(f"{label}: {count}", flush=True)
        errors.extend(failures)
    if args.source_ref:
        count, failures = check_source(args.source_ref)
        print(f"Scientific source files compared: {count}", flush=True)
        errors.extend(failures)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Repository checks passed.", flush=True)
    if args.tests:
        return subprocess.run(
            [sys.executable, "-m", "pytest", *SMOKE_TESTS], cwd=PACKAGE, check=False
        ).returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
