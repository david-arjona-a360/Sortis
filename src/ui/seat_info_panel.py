from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame,
)


class SeatInfoPanel(QWidget):
    request_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._total = 0
        self._occupied = 0
        self._vacant = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header = QLabel("Seat Information")
        header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(header)

        self._content = QVBoxLayout()
        self._content.setContentsMargins(0, 0, 0, 0)
        self._content.setSpacing(6)
        layout.addLayout(self._content, stretch=1)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        actions_header = QLabel("Actions")
        actions_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        actions_header.setStyleSheet("color: #555;")
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
            QPushButton:disabled { background: #bdbdbd; color: #757575; }
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

    def _add_info_row(self, label, value):
        if not value:
            return
        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #888; margin-top: 4px;")
        self._content.addWidget(lbl)
        val = QLabel(value)
        val.setFont(QFont("Segoe UI", 10))
        val.setWordWrap(True)
        val.setStyleSheet("color: #222;")
        val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._content.addWidget(val)

    def _add_section_divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("margin: 4px 0;")
        self._content.addWidget(line)

    def show_seat_info(self, seat_data):
        self._clear_content()
        person = seat_data.get("person")

        self._add_info_row("Seat", f"#{seat_data['seat_no']}")

        if person:
            dept = person.get("department") or seat_data.get("department")
            if dept:
                self._add_info_row("Department", dept)

            self._add_section_divider()

            name = person.get("name", "")
            if name:
                self._add_info_row("Employee", name)

            email = person.get("email", "")
            if email:
                self._add_info_row("Email", email)

            title = person.get("title", "")
            if title:
                self._add_info_row("Position", title)

            if seat_data.get("brigadista"):
                self._add_info_row("Brigadista", seat_data["brigadista"])

            if seat_data.get("notas"):
                self._add_info_row("Notes", seat_data["notas"])

            self._add_section_divider()
            status = QLabel("Status: Occupied")
            status.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            status.setStyleSheet("color: #2e7d32; margin-top: 4px;")
            self._content.addWidget(status)
        else:
            self._add_section_divider()
            status = QLabel("Status: VACANT")
            status.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            status.setStyleSheet("color: #e65100; margin-top: 4px;")
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
        lbl.setStyleSheet("color: #999; padding: 20px 0;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content.addWidget(lbl)

        if self._total > 0:
            stats = QLabel(
                f"Total Seats: {self._total}\n"
                f"Occupied: {self._occupied}\n"
                f"Vacant: {self._vacant}"
            )
            stats.setFont(QFont("Segoe UI", 10))
            stats.setStyleSheet("color: #bbb;")
            stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._content.addWidget(stats)

        self._content.addStretch()

    def set_stats(self, total, occupied, vacant):
        self._total = total
        self._occupied = occupied
        self._vacant = vacant
