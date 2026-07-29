from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QPushButton, QComboBox,
)

from src.core.request_store import RequestStore

_BTN_ACTIVE = """
    QPushButton {
        background: #1a237e; color: #fff; font-weight: 700;
        border: 1px solid #1a237e; padding: 5px 10px; font-size: 11px;
    }
"""
_BTN_INACTIVE = """
    QPushButton {
        background: #e0e0e0; color: #555; font-weight: 500;
        border: 1px solid #ccc; padding: 5px 10px; font-size: 11px;
    }
    QPushButton:hover { background: #d0d0d0; }
"""


class RequestPanel(QWidget):
    def __init__(self, store: RequestStore, parent=None):
        super().__init__(parent)
        self.store = store
        self._requests = []
        self.on_filter_changed = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        header = QLabel("Requests")
        header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(header)

        filter_label = QLabel("Occupancy")
        filter_label.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        filter_label.setStyleSheet("color: #888; text-transform: uppercase; margin-top: 4px;")
        layout.addWidget(filter_label)

        seg_layout = QHBoxLayout()
        seg_layout.setContentsMargins(0, 0, 0, 0)
        seg_layout.setSpacing(0)
        self.btn_all = QPushButton("All")
        self.btn_occupied = QPushButton("Occupied")
        self.btn_vacant = QPushButton("Vacant")
        for b in (self.btn_all, self.btn_occupied, self.btn_vacant):
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(_BTN_INACTIVE)
            seg_layout.addWidget(b)
        self._filter_btns = [self.btn_all, self.btn_occupied, self.btn_vacant]
        self.btn_all.setChecked(True)
        self.btn_all.setStyleSheet(_BTN_ACTIVE)
        self.btn_all.clicked.connect(lambda: self._set_occupancy("all"))
        self.btn_occupied.clicked.connect(lambda: self._set_occupancy("occupied"))
        self.btn_vacant.clicked.connect(lambda: self._set_occupancy("vacant"))
        layout.addLayout(seg_layout)

        self.dept_filter = QComboBox()
        self.dept_filter.addItem("All Departments")
        self.dept_filter.currentTextChanged.connect(self._emit_filter)
        layout.addWidget(self.dept_filter)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget, stretch=1)

        btn_row = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        btn_row.addWidget(refresh_btn)
        layout.addLayout(btn_row)

        self._detail = QLabel("Select a request to view details")
        self._detail.setWordWrap(True)
        self._detail.setFont(QFont("Segoe UI", 9))
        layout.addWidget(self._detail)

    def _set_occupancy(self, value):
        for b in self._filter_btns:
            active = b.text().lower() == value
            b.setChecked(active)
            b.setStyleSheet(_BTN_ACTIVE if active else _BTN_INACTIVE)
        self._emit_filter()

    def _emit_filter(self):
        occ = "all"
        for b in self._filter_btns:
            if b.isChecked():
                occ = b.text().lower()
        dept = self.dept_filter.currentText()
        if self.on_filter_changed:
            self.on_filter_changed(occ, dept)

    def refresh(self):
        self._requests = self.store.list_all()
        self._filter()

    def set_departments(self, dept_list):
        current = self.dept_filter.currentText()
        self.dept_filter.blockSignals(True)
        self.dept_filter.clear()
        self.dept_filter.addItem("All Departments")
        for d in sorted(dept_list):
            self.dept_filter.addItem(d)
        idx = self.dept_filter.findText(current)
        if idx >= 0:
            self.dept_filter.setCurrentIndex(idx)
        self.dept_filter.blockSignals(False)

    def _filter(self):
        dept = self.dept_filter.currentText()
        self.list_widget.clear()
        for req in self._requests:
            if dept != "All Departments" and req.department != dept:
                continue
            text = f"{req.id}\n{req.requestor_name} - Seat #{req.position}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, req.id)
            self.list_widget.addItem(item)
        self.list_widget.addItem(f"--- {self.list_widget.count()} requests ---")
        if self.list_widget.count() == 1:
            self.list_widget.clear()
            self.list_widget.addItem("No requests found")

    def _on_item_clicked(self, item):
        req_id = item.data(Qt.ItemDataRole.UserRole)
        if not req_id:
            return
        req = self.store.get(req_id)
        if req:
            self._detail.setText(
                f"<b>ID:</b> {req.id}<br>"
                f"<b>Date:</b> {req.date}<br>"
                f"<b>Requestor:</b> {req.requestor_name}<br>"
                f"<b>Email:</b> {req.requestor_email}<br>"
                f"<b>Department:</b> {req.department}<br>"
                f"<b>Position:</b> Seat #{req.position}<br>"
                f"<b>Current:</b> {req.current_employee or 'N/A'}<br>"
                f"<b>Proposed:</b> {req.proposed_employee}"
            )
