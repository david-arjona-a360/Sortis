from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QLabel, QPushButton,
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
        self.search.setPlaceholderText("Search requests...")
        self.search.textChanged.connect(self._filter)
        layout.addWidget(self.search)

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
        self._filter()

    def _filter(self):
        query = self.search.text().strip().lower()
        self.list_widget.clear()
        for req in self._requests:
            if query and query not in req.id.lower() and query not in req.requestor_name.lower():
                continue
            text = f"{req.id}\n{req.requestor_name} - {req.position}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, req.id)
            self.list_widget.addItem(item)
        if self.list_widget.count() == 0:
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
                f"<b>Department:</b> {req.department}<br>"
                f"<b>Position:</b> {req.position}<br>"
                f"<b>Current:</b> {req.current_employee or 'N/A'}<br>"
                f"<b>Proposed:</b> {req.proposed_employee}"
            )
