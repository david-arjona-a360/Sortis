"""
Startup environment validation and onboarding tests.

Verifies the startup gate classification (validate_environment) and the
first-run onboarding marker without requiring a real OneDrive setup.

Run:
    python tests/test_startup_check.py

Exit code:
    0 -- All tests passed
    1 -- Some tests failed
"""

import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.startup_check import validate_environment
from src.core import onboarding

PASS = 0
FAIL = 0
ERRORS = []


def report(test_name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {test_name}")
    else:
        FAIL += 1
        ERRORS.append((test_name, detail))
        print(f"  [FAIL] {test_name} -- {detail}")


class FakeQMessageBox:
    information_calls = []

    @staticmethod
    def information(parent, title, text):
        FakeQMessageBox.information_calls.append((title, text))
        return 0


def make_floor_plan(root, positions_content):
    fp = os.path.join(root, "PTY Files - Documents", "FLOOR PLAN")
    os.makedirs(fp, exist_ok=True)
    os.makedirs(os.path.join(fp, "requests"), exist_ok=True)
    with open(os.path.join(fp, "positions.json"), "w", encoding="utf-8") as fh:
        fh.write(positions_content)
    return fp


def test_01_blocked_when_onedrive_missing():
    print("\n1. Gate blocks when OneDrive/FLOOR PLAN are missing")
    os.environ["SORTIS_ONEDRIVE_OVERRIDE"] = os.path.join(tempfile.gettempdir(), "sortis_missing_root")
    v = validate_environment()
    critical_names = [c["name"] for c in v.critical]
    report("Blocked when root missing", v.is_blocked, str(critical_names))
    report("Critical includes OneDrive root check", "OneDrive root found" in critical_names)
    report("Critical includes FLOOR PLAN check", "FLOOR PLAN folder exists" in critical_names)


def test_02_passes_with_valid_floor_plan():
    print("\n2. Gate passes with a valid FLOOR PLAN")
    valid = {
        "grid": {"rows": 2, "cols": 2},
        "rooms": [],
        "seats": [],
        "departments": [],
    }
    root = tempfile.mkdtemp(prefix="sortis_startup_check_")
    try:
        os.environ["SORTIS_ONEDRIVE_OVERRIDE"] = root
        make_floor_plan(root, json.dumps(valid))
        v = validate_environment()
        report("Not blocked with valid setup", not v.is_blocked, v.critical_messages())
        report("All health checks pass", v.result.all_pass, v.result.summary())
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_03_onboarding_first_run_only():
    print("\n3. Onboarding guidance shows only on first run")
    onboarding.QMessageBox = FakeQMessageBox
    tmp = tempfile.mkdtemp(prefix="sortis_onboarding_")
    try:
        os.environ["LOCALAPPDATA"] = tmp
        config_file = os.path.join(tmp, "SORTIS", "config.json")
        FakeQMessageBox.information_calls.clear()

        report("First run detected without marker", onboarding.is_first_run())

        onboarding.run()
        report("Guidance dialog shown once",
               len(FakeQMessageBox.information_calls) == 1)
        if FakeQMessageBox.information_calls:
            title, text = FakeQMessageBox.information_calls[0]
            report("Dialog title is Setup Requirements",
                   title == "Setup Requirements", title)
            report("Dialog mentions FLOOR PLAN",
                   "FLOOR PLAN" in text, text)
        report("Marker written after guidance", os.path.exists(config_file))
        report("Not first run after marker", not onboarding.is_first_run())

        onboarding.run()
        report("Guidance NOT shown on second run",
               len(FakeQMessageBox.information_calls) == 1)

        os.remove(config_file)
        report("First run detected again after marker deleted", onboarding.is_first_run())
    finally:
        os.environ.pop("LOCALAPPDATA", None)
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=" * 60)
    print("  Startup validation & onboarding tests")
    print("=" * 60)

    try:
        test_01_blocked_when_onedrive_missing()
        test_02_passes_with_valid_floor_plan()
        test_03_onboarding_first_run_only()
    finally:
        os.environ.pop("SORTIS_ONEDRIVE_OVERRIDE", None)

    print("\n" + "=" * 60)
    print(f"  Results: {PASS} passed, {FAIL} failed")
    if FAIL:
        print("  Failures:")
        for name, detail in ERRORS:
            print(f"    - {name}: {detail}")
    print("=" * 60)

    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
