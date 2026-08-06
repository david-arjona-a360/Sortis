"""Startup environment validation for SORTIS.

Promotes the non-blocking health check into a classification that a
startup gate can use to decide whether the application may start.

Critical failures make the app unusable (OneDrive root or the FLOOR PLAN
folder is missing) and block startup. Warnings (missing/corrupt map data,
requests folder issues) let the app start but should be surfaced to the
user through the status bar.
"""

from .health_check import run_health_check

CRITICAL_CHECK_NAMES = {
    "OneDrive root found",
    "FLOOR PLAN folder exists",
}


class StartupValidation:
    def __init__(self, result=None):
        self.result = result if result is not None else run_health_check()
        self.critical = []
        self.warnings = []
        for failure in self.result.failures():
            if failure["name"] in CRITICAL_CHECK_NAMES:
                self.critical.append(failure)
            else:
                self.warnings.append(failure)

    @property
    def is_blocked(self):
        return len(self.critical) > 0

    def critical_messages(self):
        return [f["error"] for f in self.critical]

    def warning_messages(self):
        return [f["error"] for f in self.warnings]


def validate_environment():
    """Run the health checks and classify failures as critical or warnings."""
    return StartupValidation(run_health_check())
