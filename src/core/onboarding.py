"""First-run onboarding for SORTIS.

Shows a one-time "Setup Requirements" message explaining which OneDrive
folder the application needs. First-run state is persisted in a small
config file under LOCALAPPDATA\\SORTIS\\config.json, mirroring the
onboarding experience of the inventory application.
"""

import os
import json
from datetime import datetime

from PySide6.QtWidgets import QMessageBox

SETUP_REQUIREMENTS_TITLE = "Setup Requirements"
SETUP_REQUIREMENTS_MESSAGE = (
    "This application requires access to the following OneDrive/SharePoint folder:\n\n"
    "    - PTY Files - Documents\\FLOOR PLAN\n\n"
    "Please ensure:\n\n"
    "    1. OneDrive is synchronized\n"
    "    2. This folder exists in your OneDrive\n"
    "    3. Files are available locally (not cloud-only)\n\n"
    "If this folder is missing, the application will not function correctly."
)


def _config_file():
    base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    return os.path.join(base, "SORTIS", "config.json")


def is_first_run():
    return not os.path.exists(_config_file())


def mark_first_run_done():
    config_file = _config_file()
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    config = {
        "first_run_complete": True,
        "first_run_date": datetime.now().isoformat(),
    }
    with open(config_file, "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2)


def show_setup_requirements():
    QMessageBox.information(None, SETUP_REQUIREMENTS_TITLE, SETUP_REQUIREMENTS_MESSAGE)


def run():
    if is_first_run():
        show_setup_requirements()
        mark_first_run_done()
