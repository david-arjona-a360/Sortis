from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame,
)

_PANEL_BG = "#1e1e1e"
_LABEL_COLOR = "#aaa"
_VALUE_COLOR = "#ffffff"
_HEADER_COLOR = "#ffffff"
_ACTIONS_COLOR = "#aaa"
_PLACEHOLDER_COLOR = "#aaa"
_STATS_COLOR = "#777"
_SEPARATOR_COLOR = "#444"
_OCCUPIED_COLOR = "#4caf50"
_VACANT_COLOR = "#ff9800"
_DEPT_COLOR = "#5c8aff"
_FALLBACK_COLOR = "#666"


class SeatInfoPanel(QWidget):
    request_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._total = 0
        self._occupied = 0
        self._vacant = 0
        self._setup_ui()

    def _setup_ui(self):
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(_PANEL_BG))
        self.setPalette(pal)
        self.setAutoFillBackground(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header = QLabel("Seat Information")
        header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {_HEADER_COLOR};")
        layout.addWidget(header)

        self._content = QVBoxLayout()
        self._content.setContentsMargins(0, 0, 0, 0)
        self._content.setSpacing(6)
        layout.addLayout(self._content, stretch=1)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet(f"color: {_SEPARATOR_COLOR};")
        layout.addWidget(line)

        actions_header = QLabel("Actions")
        actions_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        actions_header.setStyleSheet(f"color: {_ACTIONS_COLOR};")
        layout.addWidget(actions_header)

        self.request_btn = QPushButton("Request Change for Selected Seat")
        self.request_btn.setEnabled(False)
        self.request_btn.setStyleSheet("""
            QPushButton {
                background: #1a237e; color: #fff; font-weight: 700;
                border: none; padding: 8px 16px; border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover { background: #283593; }
            QPushButton:disabled { background: #3a3a3a; color: #777; }
        """)
        self.request_btn.clicked.connect(self.request_clicked.emit)
        layout.addWidget(self.request_btn)

        self._show_placeholder()

    def _clear_content(self):
        while self._content.count():
            item = self._content.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _add_info_row(self, label, value, value_color=None, fallback=None):
        if not value:
            if fallback:
                value = fallback
                if value_color is None:
                    value_color = _FALLBACK_COLOR
            else:
                return
        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {_LABEL_COLOR}; margin-top: 4px;")
        self._content.addWidget(lbl)
        val = QLabel(value)
        val.setFont(QFont("Segoe UI", 10))
        val.setWordWrap(True)
        val_color = value_color or _VALUE_COLOR
        val.setStyleSheet(f"color: {val_color};")
        val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._content.addWidget(val)

    def _add_section_divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet(f"color: {_SEPARATOR_COLOR}; margin: 4px 0;")
        self._content.addWidget(line)

    def show_seat_info(self, seat_data):
        self._clear_content()
        person = seat_data.get("person")

        self._add_info_row("Seat", f"#{seat_data['seat_no']}")

        if person:
            dept = person.get("department") or seat_data.get("department")
            self._add_info_row("Department", dept, _DEPT_COLOR, "Not assigned")

            self._add_section_divider()

            name = person.get("name", "")
            self._add_info_row("Employee", name)

            email = person.get("email", "")
            self._add_info_row("Email", email, fallback="Not provided")

            title = person.get("title", "")
            self._add_info_row("Position", title, fallback="Not specified")

            brig = seat_data.get("brigadista")
            self._add_info_row("Brigadista", brig, fallback="None")

            notas = seat_data.get("notas")
            self._add_info_row("Notes", notas, fallback="None")

            self._add_section_divider()
            status = QLabel("Status: Occupied")
            status.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            status.setStyleSheet(f"color: {_OCCUPIED_COLOR}; margin-top: 4px;")
            self._content.addWidget(status)
        else:
            self._add_section_divider()
            status = QLabel("Status: VACANT")
            status.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            status.setStyleSheet(f"color: {_VACANT_COLOR}; margin-top: 4px;")
            self._content.addWidget(status)

        self._content.addStretch()
        self.request_btn.setEnabled(True)

    def clear_selection(self):
        self._clear_content()
        self._show_placeholder()
        self.request_btn.setEnabled(False)

    def _show_placeholder(self):
        lbl = QLabel("Select a seat\nto view information")
        lbl.setFont(QFont("Segoe UI", 12))
        lbl.setStyleSheet(f"color: {_PLACEHOLDER_COLOR}; padding: 20px 0;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content.addWidget(lbl)

        if self._total > 0:
            stats = QLabel(
                f"Total Seats: {self._total}\n"
                f"Occupied: {self._occupied}\n"
                f"Vacant: {self._vacant}"
            )
            stats.setFont(QFont("Segoe UI", 10))
            stats.setStyleSheet(f"color: {_STATS_COLOR};")
            stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._content.addWidget(stats)

        self._content.addStretch()

    def set_stats(self, total, occupied, vacant):
        self._total = total
        self._occupied = occupied
        self._vacant = vacant
