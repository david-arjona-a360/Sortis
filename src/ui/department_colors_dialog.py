import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox, QHeaderView, QColorDialog,
)

from src.core.color_manager import (
    DeptColorManager,
    _FALLBACK_DEPT_COLORS,
    _FALLBACK_DEFAULT_COLOR,
)
from src.core.file_utils import AtomicWriteError
from src.theme.theme import BORDER_COLOR
from src.ui.dialog_theme import apply_dialog_theme, style_button

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

_DEFAULT_ROW = "Default (unlisted)"


class DepartmentColorsDialog(QDialog):
    """Visual editor for config/dept_colors.json.

    Changes live in memory until Save. Save writes atomically to the shared
    OneDrive config (single source of truth) and reloads the manager.
    """

    def __init__(self, departments, parent=None):
        super().__init__(parent)
        self.departments = sorted(departments)
        self._colors = dict(DeptColorManager.get_all_colors())
        self._default = DeptColorManager.get_default_color()
        self._dirty = False
        self.saved = False

        self.setWindowTitle("Admin - Department Colors")
        self.resize(560, 480)
        apply_dialog_theme(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        title = QLabel("Department Colors")
        title.setProperty("role", "title")
        layout.addWidget(title)

        self._warning = QLabel()
        self._warning.setWordWrap(True)
        self._warning.setStyleSheet("color: #f9a825; background: transparent;")
        self._warning.setText(
            "Config file missing or corrupt - showing built-in defaults. "
            "Press Save to create the configuration."
        )
        layout.addWidget(self._warning)
        self._warning.setVisible(DeptColorManager.get_source() == "built-in fallback")

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Department", "Color Preview", "Hex"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.cellDoubleClicked.connect(self._change_color)
        layout.addWidget(self.table, stretch=1)

        self._status_label = QLabel()
        self._status_label.setWordWrap(True)
        self._status_label.setStyleSheet("color: #8a8a8a; background: transparent;")
        layout.addWidget(self._status_label)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        self.btn_change = QPushButton("Change Color...")
        style_button(self.btn_change)
        self.btn_restore = QPushButton("Restore Defaults")
        style_button(self.btn_restore)
        buttons.addWidget(self.btn_change)
        buttons.addWidget(self.btn_restore)
        buttons.addStretch(1)
        self.btn_save = QPushButton("Save")
        style_button(self.btn_save, "primary")
        self.btn_close = QPushButton("Close")
        style_button(self.btn_close)
        buttons.addWidget(self.btn_save)
        buttons.addWidget(self.btn_close)
        layout.addLayout(buttons)

        self.btn_change.clicked.connect(self._change_color)
        self.btn_restore.clicked.connect(self._restore_defaults)
        self.btn_save.clicked.connect(self._save)
        self.btn_close.clicked.connect(self._close)

        self._rebuild_rows()
        self.btn_save.setEnabled(False)
        self._status_label.setText(
            "Edits apply on Save. Close discards unsaved changes."
        )

    def _entries(self):
        yield _DEFAULT_ROW, None
        for dept in self.departments:
            if dept and dept != _DEFAULT_ROW:
                yield dept, dept

    def _hex_for(self, name, key):
        return self._default if key is None else self._colors.get(key, self._default)

    def _rebuild_rows(self):
        self.table.setRowCount(0)
        for name, key in self._entries():
            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.table.setItem(row, 0, name_item)

            swatch = QLabel()
            swatch.setFixedSize(44, 18)
            swatch.setStyleSheet(
                f"background-color: {self._hex_for(name, key)}; "
                f"border: 1px solid {BORDER_COLOR}; border-radius: 3px;"
            )
            self.table.setCellWidget(row, 1, swatch)

            hex_item = QTableWidgetItem(self._hex_for(name, key).upper())
            hex_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            hex_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, hex_item)

        self.table.selectRow(0)
        self.table.setColumnWidth(1, 56)
        self.table.setColumnWidth(2, 110)

    def _current_row(self):
        row = self.table.currentRow()
        if not (0 <= row < self.table.rowCount()):
            return None
        return row

    def _change_color(self, *_):
        row = self._current_row()
        if row is None:
            return
        name, key = list(self._entries())[row]
        current = self._hex_for(name, key)
        color = QColorDialog.getColor(QColor(current), self, f"Color for {name}")
        if not color.isValid() or not color.name().startswith("#"):
            return
        hex_value = color.name().upper()
        if hex_value == current.upper():
            return

        if key is None:
            self._default = hex_value
        else:
            self._colors[key] = hex_value
        self._apply_row(row, name, key)
        self._mark_dirty("Press Save to apply changes.")

    def _apply_row(self, row, name, key):
        hex_value = self._hex_for(name, key).upper()
        self.table.item(row, 2).setText(hex_value)
        swatch = self.table.cellWidget(row, 1)
        swatch.setStyleSheet(
            f"background-color: {hex_value}; "
            f"border: 1px solid {BORDER_COLOR}; border-radius: 3px;"
        )

    def _mark_dirty(self, message):
        self._dirty = True
        self.saved = False
        self.btn_save.setEnabled(True)
        self._status_label.setText(message)

    def _save(self):
        try:
            DeptColorManager.save(self._colors, self._default)
        except (AtomicWriteError, OSError) as exc:
            QMessageBox.critical(
                self, "Save Failed",
                f"Could not save the color configuration:\n{exc}",
            )
            return
        self._dirty = False
        self.saved = True
        self.btn_save.setEnabled(False)
        self._status_label.setText(f"Saved to {DeptColorManager.get_source()}")

    def _restore_defaults(self):
        answer = QMessageBox.question(
            self, "Restore Defaults",
            "Reset all department colors to the built-in defaults?\n"
            "Press Save to apply.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._colors = dict(_FALLBACK_DEPT_COLORS)
        self._default = _FALLBACK_DEFAULT_COLOR
        self._rebuild_rows()
        self._mark_dirty("Defaults loaded - press Save to apply.")

    def _close(self):
        if self._dirty:
            answer = QMessageBox.question(
                self, "Discard Changes",
                "You have unsaved color changes.\nDiscard them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.accept()

    def closeEvent(self, event):
        if self._dirty:
            answer = QMessageBox.question(
                self, "Discard Changes",
                "You have unsaved color changes.\nDiscard them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        super().closeEvent(event)
