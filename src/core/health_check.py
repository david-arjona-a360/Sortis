import os
import json

from .path_config import (
    find_onedrive_root, get_floor_plan_path,
    get_positions_path, get_requests_path
)


class HealthCheckResult:
    def __init__(self):
        self.checks = []
        self.all_pass = True

    def add(self, name, passed, error=None):
        self.checks.append({"name": name, "pass": passed, "error": error})
        if not passed:
            self.all_pass = False

    def summary(self):
        passed = sum(1 for c in self.checks if c["pass"])
        failed = len(self.checks) - passed
        return f"{passed}/{len(self.checks)} checks passed" + (f", {failed} failed" if failed else "")

    def failures(self):
        return [c for c in self.checks if not c["pass"]]


def run_health_check():
    result = HealthCheckResult()

    root = find_onedrive_root()
    result.add("OneDrive root found", root is not None,
               "OneDrive folder not found. Ensure OneDrive is installed and syncing.")

    if root:
        floor_plan = get_floor_plan_path()
        result.add("FLOOR PLAN folder exists", floor_plan and os.path.isdir(floor_plan),
                   f"FLOOR PLAN folder not found at: {floor_plan}")

        positions = get_positions_path()
        positions_ok = positions and os.path.isfile(positions)
        result.add("positions.json exists", positions_ok,
                   f"positions.json not found at: {positions}")

        if positions_ok:
            try:
                with open(positions, "r", encoding="utf-8") as f:
                    data = json.load(f)
                valid = isinstance(data, dict) and "seats" in data and "grid" in data
                result.add("positions.json valid", valid,
                           "positions.json missing required keys (seats, grid)")
            except (json.JSONDecodeError, IOError) as e:
                result.add("positions.json valid", False, str(e))

        requests_dir = get_requests_path()
        requests_ok = requests_dir and os.path.isdir(requests_dir)
        result.add("requests/ directory exists", requests_ok,
                   f"requests/ not found at: {requests_dir}")

        if requests_dir:
            writable = os.access(requests_dir, os.W_OK) if os.path.isdir(requests_dir) else False
            result.add("requests/ writable", writable,
                      "No write permission to requests/ directory")

    return result
