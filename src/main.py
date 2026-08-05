import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from src.core.color_manager import DeptColorManager
from src.core.auth_manager import AuthManager
from src.ui.main_window import MainWindow


def main():
    DeptColorManager.load()
    AuthManager.load()
    app = QApplication(sys.argv)
    app.setApplicationName("Interactive Office Map")
    app.setOrganizationName("a360inc")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
