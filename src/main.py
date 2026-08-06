import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QMessageBox
from src.core.color_manager import DeptColorManager
from src.core.auth_manager import AuthManager
from src.core.onboarding import run as run_onboarding
from src.core.startup_check import validate_environment
from src.ui.main_window import MainWindow


def _show_blocking_error(validation):
    details = "\n".join(f"    - {message}" for message in validation.critical_messages())
    QMessageBox.critical(
        None,
        "Configuration Error",
        "Required OneDrive/SharePoint folder not found.\n"
        "Please verify your OneDrive setup.\n\n"
        f"{details}\n\n"
        "Make sure OneDrive is running and signed in with your a360inc account, "
        "and that the required folders are available locally "
        "(right-click the folder in OneDrive -> 'Always keep on this device').",
    )


def main():
    DeptColorManager.load()
    AuthManager.load()
    app = QApplication(sys.argv)
    app.setApplicationName("Interactive Office Map")
    app.setOrganizationName("a360inc")

    run_onboarding()

    validation = validate_environment()
    if validation.is_blocked:
        _show_blocking_error(validation)
        sys.exit(1)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
