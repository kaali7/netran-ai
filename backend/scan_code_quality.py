"""
Netran AI — Code Quality & Architecture Audit Scanner
Script: scan_code_quality.py
Description: Automated audit scanner verifying docstrings, single root requirements.txt,
             test output folder isolation, and absence of dead prototype files.
"""

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
MODEL_DIR = BACKEND_DIR / "model"

def run_audit():
    print("===================================================================")
    print("          NETRAN AI — BACKEND CODE QUALITY AUDIT SCANNER           ")
    print("===================================================================\n")
    
    passed = True
    checks_count = 0

    # 1. Check Root requirements.txt
    checks_count += 1
    root_req = BACKEND_DIR / "requirements.txt"
    if root_req.exists():
        print("  [PASS] Root requirements.txt exists.")
    else:
        print("  [FAIL] Missing root requirements.txt!")
        passed = False

    # 2. Check per-stage requirements.txt are deleted
    checks_count += 1
    stage_reqs = list(MODEL_DIR.glob("**/requirements.txt"))
    if not stage_reqs:
        print("  [PASS] No redundant per-stage requirements.txt files found.")
    else:
        print(f"  [FAIL] Found redundant per-stage requirements.txt: {[str(r) for r in stage_reqs]}")
        passed = False

    # 3. Check dead model/test/ folder is deleted
    checks_count += 1
    test_folder = MODEL_DIR / "test"
    if not test_folder.exists():
        print("  [PASS] Obsolete model/test/ prototype folder is deleted.")
    else:
        print("  [FAIL] model/test/ folder still exists!")
        passed = False

    # 4. Check stale root logs are cleaned
    checks_count += 1
    stale_logs = list(MODEL_DIR.glob("**/interview_log.txt"))
    # Allow inside test_output only
    invalid_logs = [l for l in stale_logs if "test_output" not in str(l)]
    if not invalid_logs:
        print("  [PASS] No stale log files in module root folders.")
    else:
        print(f"  [FAIL] Stale log files found: {[str(l) for l in invalid_logs]}")
        passed = False

    # 5. Check module-level docstrings in python files
    checks_count += 1
    py_files = [p for p in MODEL_DIR.glob("**/*.py") if "__pycache__" not in str(p)]
    missing_docstrings = []
    
    for py_file in py_files:
        with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().strip()
            if not (content.startswith('"""') or content.startswith("'''")):
                missing_docstrings.append(py_file.name)
                
    if not missing_docstrings:
        print(f"  [PASS] All {len(py_files)} Python files contain valid module docstrings.")
    else:
        print(f"  [WARN] Python files missing docstrings ({len(missing_docstrings)}): {missing_docstrings}")

    print("\n-------------------------------------------------------------------")
    if passed and not missing_docstrings:
        print("  RESULT: ALL AUDIT CHECKS PASSED SUCCESSFULLY! [OK]")
    elif passed:
        print("  RESULT: PASSED WITH WARNINGS (Check docstrings) [WARN]")
    else:
        print("  RESULT: AUDIT FAILED — PLEASE REVIEW ISSUES ABOVE. [ERROR]")
    print("===================================================================\n")
    return passed

if __name__ == "__main__":
    success = run_audit()
    sys.exit(0 if success else 1)
