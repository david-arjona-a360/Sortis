"""Admin dialog for editing room names on the floor plan."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox,
)

from src.ui.dialog_theme import apply_dialog_theme, style_button

_MAX_NAME_LEN = 50


class RoomNameDialog(QDialog):
    """Modal dialog to set or edit a room name.

    Args:
        room_data: dict from positions.json rooms array
        existing_names: set of current room names (case-insensitive) for duplicate check
        parent: parent widget
    """

    def __init__(self, room_data, existing_names=None, parent=None):
        super().__init__(parent)
        self.room_data = room_data
        self._existing = {n.lower() for n in (existing_names or set())}
        self._original = room_data.get("name", "").strip()
        self._existing.discard(self._original.lower())
        self._new_name = None

        self.setWindowTitle("Admin - Edit Room Name")
        self.setMinimumWidth(380)
        self.setModal(True)
        apply_dialog_theme(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        title = QLabel("Edit Room Name")
        title.setProperty("role", "title")
        layout.addWidget(title)

        geo = "rows %d-%d, cols %d-%d" % (
            room_data["min_row"], room_data["max_row"],
            room_data["min_col"], room_data["max_col"],
        )
        geo_label = QLabel("Room geometry: %s" % geo)
        geo_label.setStyleSheet("color: #8a8a8a; background: transparent;")
        layout.addWidget(geo_label)

        name_label = QLabel("Room Name:")
        name_label.setProperty("role", "section")
        layout.addWidget(name_label)

        self.input = QLineEdit(self._original)
        self.input.setPlaceholderText("Enter room name")
        self.input.setMaxLength(_MAX_NAME_LEN)
        layout.addWidget(self.input)

        self._status = QLabel()
        self._status.setWordWrap(True)
        self._status.setStyleSheet("background: transparent;")
        layout.addWidget(self._status)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        self.btn_save = QPushButton("Save")
        style_button(self.btn_save, "primary")
        self.btn_cancel = QPushButton("Cancel")
        style_button(self.btn_cancel)
        buttons.addStretch(1)
        buttons.addWidget(self.btn_save)
        buttons.addWidget(self.btn_cancel)
        layout.addLayout(buttons)

        self.btn_save.clicked.connect(self._on_save)
        self.btn_cancel.clicked.connect(self.reject)
        self.input.returnPressed.connect(self._on_save)
        self.input.setFocus()

    @property
    def new_name(self):
        """The new name if accepted, else None."""
        return self._new_name

    def _validate(self, name):
        if not name:
            return "Room name cannot be empty."
        if len(name) > _MAX_NAME_LEN:
            return "Name too long (max %d characters)." % _MAX_NAME_LEN
        if name.lower() in self._existing:
            return "A room with this name already exists."
        return None

    def _on_save(self):
        name = self.input.text().strip()
        err = self._validate(name)
        if err:
            self._status.setText(err)
            self._status.setStyleSheet("color: #f9a825; background: transparent;")
            return
        self._new_name = name
        self.accept()
