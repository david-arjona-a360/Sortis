from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QComboBox, QPushButton, QLabel, QMessageBox, QHeaderView,
)

from src.core.auth_manager import AuthManager
from src.core.exporter import export_to_pdf, export_to_xlsx
from src.models.request import (
    STATUS_PENDING, STATUS_COMPLETED, STATUS_CANCELLED,
)

_STATUS_LABELS = {
    STATUS_PENDING: "Pending",
    STATUS_COMPLETED: "Completed",
    STATUS_CANCELLED: "Cancelled",
}

_STATUS_COLORS = {
    STATUS_PENDING: QColor("#b8860b"),
    STATUS_COMPLETED: QColor("#2e7d32"),
    STATUS_CANCELLED: QColor("#c62828"),
}


class AdminRequestsDialog(QDialog):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        self.requests = []

        self.setWindowTitle("Admin - Request Management")
        self.resize(1000, 540)

        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Status:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Pending", "Completed", "Cancelled"])
        self.filter_combo.currentTextChanged.connect(self._refresh)
        top.addWidget(self.filter_combo)
        top.addStretch(1)
        layout.addLayout(top)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Date", "Requestor", "Department", "Seat", "Proposed", "Status"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self._update_selection)
        layout.addWidget(self.table, stretch=1)

        self.details = QLabel()
        self.details.setWordWrap(True)
        self.details.setTextFormat(Qt.TextFormat.RichText)
        self.details.setStyleSheet("color: #444;")
        layout.addWidget(self.details)

        buttons = QHBoxLayout()
        self.btn_complete = QPushButton("Mark Completed")
        self.btn_cancel = QPushButton("Mark Cancelled")
        self.btn_reopen = QPushButton("Reopen")
        self.btn_pdf = QPushButton("Export PDF")
        self.btn_xlsx = QPushButton("Export Excel")
        self.btn_refresh = QPushButton("Refresh")
        self.btn_close = QPushButton("Close")

        for btn in (self.btn_complete, self.btn_cancel, self.btn_reopen,
                    self.btn_pdf, self.btn_xlsx, self.btn_refresh, self.btn_close):
            buttons.addWidget(btn)

        self.btn_complete.clicked.connect(lambda: self._set_status(STATUS_COMPLETED))
        self.btn_cancel.clicked.connect(lambda: self._set_status(STATUS_CANCELLED))
        self.btn_reopen.clicked.connect(lambda: self._set_status(STATUS_PENDING))
        self.btn_pdf.clicked.connect(self._export_pdf)
        self.btn_xlsx.clicked.connect(self._export_xlsx)
        self.btn_refresh.clicked.connect(self._refresh)
        self.btn_close.clicked.connect(self.accept)

        layout.addLayout(buttons)

        self._refresh()

    def _refresh(self):
        if self.store is None:
            self.requests = []
        else:
            self.requests = self.store.list_all()
        status_filter = self.filter_combo.currentText().lower()
        if status_filter != "all":
            self.requests = [r for r in self.requests if r.status == status_filter]

        self.table.setRowCount(0)
        for req in self.requests:
            row = self.table.rowCount()
            self.table.insertRow(row)
            status_item = QTableWidgetItem(_STATUS_LABELS.get(req.status, req.status.capitalize()))
            status_item.setForeground(_STATUS_COLORS.get(req.status, QColor("#000")))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            values = [
                QTableWidgetItem(req.id),
                QTableWidgetItem(req.date),
                QTableWidgetItem(req.requestor_name),
                QTableWidgetItem(req.department),
                QTableWidgetItem(str(req.position)),
                QTableWidgetItem(req.proposed_employee),
                status_item,
            ]
            for col, item in enumerate(values):
                self.table.setItem(row, col, item)
        self._update_selection()

    def _selected_request(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.requests):
            return self.requests[row]
        return None

    def _update_selection(self):
        req = self._selected_request()
        if req is None:
            self.btn_complete.setEnabled(False)
            self.btn_cancel.setEnabled(False)
            self.btn_reopen.setEnabled(False)
            self.details.clear()
            return
        self.btn_complete.setEnabled(req.status != STATUS_COMPLETED)
        self.btn_cancel.setEnabled(req.status != STATUS_CANCELLED)
        self.btn_reopen.setEnabled(req.status != STATUS_PENDING)
        self._show_details(req)

    def _show_details(self, req):
        html = (
            f"<b>{req.id}</b> &mdash; {req.requestor_name} "
            f"&lt;{req.requestor_email}&gt;<br>"
            f"Dept: {req.department} | Seat: {req.position} | "
            f"Current: {req.current_employee or 'N/A'} | "
            f"Proposed: {req.proposed_employee}<br>"
            f"<b>Status:</b> {_STATUS_LABELS.get(req.status, req.status)}"
        )
        if req.resolved_at:
            html += f" | resolved by {req.resolved_by} @ {req.resolved_at}"
        self.details.setText(html)

    def _set_status(self, status):
        req = self._selected_request()
        if req is None or req.status == status:
            return
        actions = {
            STATUS_COMPLETED: "Complete",
            STATUS_CANCELLED: "Cancel",
            STATUS_PENDING: "Reopen",
        }
        if not QMessageBox.question(
            self,
            "Confirm",
            f"{actions[status]} request {req.id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes:
            return
        self.store.set_status(req.id, status, by=AuthManager.current_user())
        self._refresh()

    def _export_pdf(self):
        if not self.requests:
            QMessageBox.information(self, "Export", "No requests to export")
            return
        export_to_pdf(self.requests, self)

    def _export_xlsx(self):
        if not self.requests:
            QMessageBox.information(self, "Export", "No requests to export")
            return
        export_to_xlsx(self.requests, self)
