#!/usr/bin/env python3
"""
Run pre-production checks for The 543 static deployment.

From repository root:
    python scripts/production_check.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def run_step(label: str, command: list[str], cwd: Path | None = None) -> bool:
    print(f"\n>>> {label}")
    print(f"    {' '.join(command)}")
    result = subprocess.run(command, cwd=cwd or ROOT, check=False)
    if result.returncode != 0:
        print(f"    FAILED (exit {result.returncode})")
        return False
    print("    OK")
    return True


def main() -> int:
    print("The 543 — production build validation")
    print(f"Repository: {ROOT}")

    steps = [
        ("Build frontend data bundle", [sys.executable, "-m", "src.export.build_frontend_data_bundle"], ROOT),
        ("Deploy safety check", [sys.executable, "scripts/check_deploy_safety.py"], ROOT),
        ("Frontend TypeScript + Vite build", ["npm", "run", "build"], FRONTEND),
    ]

    for label, command, cwd in steps:
        if not run_step(label, command, cwd):
            print("\nProduction check FAILED.")
            print("\nManual commands:")
            print("  python -m src.export.build_frontend_data_bundle")
            print("  python scripts/check_deploy_safety.py")
            print("  cd frontend && npm install && npm run build && npm run preview")
            return 1

    print("\nProduction check PASSED.")
    print("Preview locally: cd frontend && npm run preview")
    print("Deploy: see frontend/DEPLOYMENT.md (Vercel root = frontend, domain = the543.org)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
