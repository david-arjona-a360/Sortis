from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QLabel, QPushButton, QComboBox,
)

from src.core.request_store import RequestStore


class RequestPanel(QWidget):
    def __init__(self, store: RequestStore, parent=None):
        super().__init__(parent)
        self.store = store
        self._requests = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        header = QLabel("Requests")
        header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(header)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search ID or requestor...")
        self.search.textChanged.connect(self._filter)
        layout.addWidget(self.search)

        self.dept_filter = QComboBox()
        self.dept_filter.addItem("All Departments")
        self.dept_filter.currentTextChanged.connect(self._filter)
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

    def refresh(self):
        self._requests = self.store.list_all()
        depts = sorted({r.department for r in self._requests if r.department})
        current = self.dept_filter.currentText()
        self.dept_filter.blockSignals(True)
        self.dept_filter.clear()
        self.dept_filter.addItem("All Departments")
        for d in depts:
            self.dept_filter.addItem(d)
        idx = self.dept_filter.findText(current)
        if idx >= 0:
            self.dept_filter.setCurrentIndex(idx)
        self.dept_filter.blockSignals(False)
        self._filter()

    def _filter(self):
        query = self.search.text().strip().lower()
        dept = self.dept_filter.currentText()
        self.list_widget.clear()
        for req in self._requests:
            if query and query not in req.id.lower() and query not in req.requestor_name.lower():
                continue
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
