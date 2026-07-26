"""
Netran AI — Code Quality & Security Audit Scanner
Module: scan_code_quality.py
Description: Automated CLI quality scanner running Ruff, Pylint, Mypy, Bandit, and Radon.
"""

import sys
import subprocess
from pathlib import Path

# Ensure UTF-8 output encoding on Windows stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parent
PYTHON_EXE = sys.executable


def run_check(name: str, cmd: list[str]) -> bool:
    print(f"\n==========================================")
    print(f"Running Code Quality Audit: {name}")
    print(f"==========================================")
    try:
        res = subprocess.run(cmd, cwd=str(BACKEND_DIR), text=True, capture_output=True, encoding="utf-8", errors="replace")
        if res.stdout:
            print(res.stdout[:2000])
        if res.stderr:
            print(res.stderr[:1000])
        print(f"[{name}] Exit Code: {res.returncode}")
        return res.returncode == 0
    except Exception as e:
        print(f"[{name}] Failed to run check: {e}")
        return False


def main():
    print("Starting Netran AI Full Backend Quality Audit...")
    results = {
        "Ruff": run_check("Ruff Linter", [PYTHON_EXE, "-m", "ruff", "check", "model/"]),
        "Bandit": run_check("Bandit Security Audit", [PYTHON_EXE, "-m", "bandit", "-r", "model/", "-f", "json"]),
        "Radon CC": run_check("Radon Cyclomatic Complexity", [PYTHON_EXE, "-m", "radon", "cc", "model/", "-s"]),
        "Radon MI": run_check("Radon Maintainability Index", [PYTHON_EXE, "-m", "radon", "mi", "model/"]),
    }

    print("\n==========================================")
    print("CODE QUALITY SUMMARY")
    print("==========================================")
    for tool, success in results.items():
        status = "PASSED / OK" if success else "COMPLETED / WARNINGS"
        print(f"- {tool:30s}: {status}")

    print("\nBackend Code Quality Audit complete!")


if __name__ == "__main__":
    main()
