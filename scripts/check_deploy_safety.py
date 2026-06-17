#!/usr/bin/env python3
"""
Scan the repo for files that must not ship in a static frontend deployment.

Run from repository root:
    python scripts/check_deploy_safety.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_PUBLIC = ROOT / "frontend" / "public"

RESTRICTED_EXTENSIONS = {
    ".dta",
    ".sav",
    ".zip",
    ".7z",
    ".rar",
    ".pdf",
}

RESTRICTED_PUBLIC_EXTENSIONS = {
    ".dta",
    ".sav",
    ".zip",
    ".7z",
    ".rar",
    ".pdf",
}

RESTRICTED_PATH_FRAGMENTS = [
    "data/behaviour-analysis",
    "data/postpoll/raw",
    "data/dhs/raw",
    "data/nfhs/raw",
    "data/raw/dhs_downloads",
    "data/demographics/raw",
]

RESTRICTED_TRACKED_PREFIXES = [
    "data/behaviour-analysis/",
    "data/postpoll/raw/",
    "data/dhs/raw/",
    "data/nfhs/raw/",
]


def _normalize_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _git_tracked_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _scan_directory(base: Path) -> list[str]:
    violations: list[str] = []
    if not base.exists():
        return violations

    for path in base.rglob("*"):
        if not path.is_file():
            continue
        rel = _normalize_path(path)
        suffix = path.suffix.lower()

        if base == FRONTEND_PUBLIC and suffix in RESTRICTED_PUBLIC_EXTENSIONS:
            violations.append(f"restricted file in frontend/public: {rel}")
            continue

        if suffix in RESTRICTED_EXTENSIONS and "frontend/public" in rel:
            violations.append(f"restricted extension in public assets: {rel}")

        for fragment in RESTRICTED_PATH_FRAGMENTS:
            if fragment in rel.replace("\\", "/"):
                if base == FRONTEND_PUBLIC:
                    violations.append(f"restricted path under frontend/public: {rel}")
                break

    return violations


def _scan_tracked_files(tracked: list[str]) -> list[str]:
    violations: list[str] = []
    for rel in tracked:
        path = rel.replace("\\", "/")
        basename = Path(path).name.lower()
        if basename in {".gitkeep", "readme.md", ".gitignore"}:
            continue
        suffix = Path(path).suffix.lower()

        for prefix in RESTRICTED_TRACKED_PREFIXES:
            if path.startswith(prefix):
                violations.append(f"restricted path tracked by git: {path}")
                break

        if path.startswith("frontend/public/") and suffix in RESTRICTED_PUBLIC_EXTENSIONS:
            violations.append(f"restricted file tracked under frontend/public: {path}")

        if suffix in {".dta", ".sav"} and path.startswith("frontend/"):
            violations.append(f"microdata file tracked under frontend/: {path}")

    return violations


def _scan_symlinks_in_public_geo() -> list[str]:
    violations: list[str] = []
    geo_dir = FRONTEND_PUBLIC / "geo"
    if not geo_dir.exists():
        return violations
    for path in geo_dir.iterdir():
        if path.is_symlink():
            violations.append(f"symlink in frontend/public/geo (use real files for Vercel): {path.name}")
    return violations


def main() -> int:
    print("Deploy safety check — The 543")
    print(f"  Root: {ROOT}")
    print()

    violations: list[str] = []
    violations.extend(_scan_directory(FRONTEND_PUBLIC))
    violations.extend(_scan_symlinks_in_public_geo())
    violations.extend(_scan_tracked_files(_git_tracked_files()))

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for item in violations:
        if item not in seen:
            seen.add(item)
            unique.append(item)

    if unique:
        print("FAIL — unsafe paths for production deployment:")
        for item in unique:
            print(f"  - {item}")
        print()
        print(f"  {len(unique)} issue(s) found. Fix before deploying to the543.org.")
        return 1

    print("PASS — no restricted raw files detected under frontend/public or git tracking.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
