from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QDialogButtonBox, QLabel, QMessageBox,
)

from src.models.request import Request
from src.core.request_store import RequestStore
from src.core.validator import find_duplicate


class RequestDialog(QDialog):
    def __init__(self, seat_data, departments, store, parent=None):
        super().__init__(parent)
        self.seat_data = seat_data
        self.store = store
        self.request = None

        self.setWindowTitle(f"Request for Seat #{seat_data['seat_no']}")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.req_id = QLineEdit()
        self.req_id.setReadOnly(True)

        self.req_date = QLineEdit()
        self.req_date.setReadOnly(True)

        self.requestor_name = QLineEdit()
        self.requestor_name.setPlaceholderText("Full name")

        self.requestor_email = QLineEdit()
        self.requestor_email.setPlaceholderText("email@company.com")

        self.department = QComboBox()
        self.department.addItems(departments)

        self.position = QLineEdit(seat_data["seat_no"])
        self.position.setReadOnly(True)
        person = seat_data.get("person")
        self.current_employee = QLineEdit(person["name"] if person else "")
        self.current_employee.setReadOnly(True)

        self.proposed_employee = QLineEdit()
        self.proposed_employee.setPlaceholderText("Proposed person name")

        form.addRow("Request ID:", self.req_id)
        form.addRow("Date:", self.req_date)
        form.addRow("Requestor Name:", self.requestor_name)
        form.addRow("Requestor Email:", self.requestor_email)
        form.addRow("Department:", self.department)
        form.addRow("Position:", self.position)
        form.addRow("Current Employee:", self.current_employee)
        form.addRow("Proposed Employee:", self.proposed_employee)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Submit")
        buttons.accepted.connect(self._on_submit)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._generate_id()

    def _generate_id(self):
        import uuid
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        date_part = now.strftime("%Y%m%d")
        unique = uuid.uuid4().hex[:6].upper()
        self.req_id.setText(f"REQ-{date_part}-{unique}")
        self.req_date.setText(now.strftime("%Y-%m-%d"))

    def _on_submit(self):
        name = self.requestor_name.text().strip()
        email = self.requestor_email.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Requestor Name is required")
            return
        if not email or "@" not in email:
            QMessageBox.warning(self, "Validation", "Valid email is required")
            return
        proposed = self.proposed_employee.text().strip()
        if not proposed:
            QMessageBox.warning(self, "Validation", "Proposed Employee is required")
            return

        dup = find_duplicate(self.store, self.seat_data["seat_no"], proposed)
        if dup:
            QMessageBox.warning(
                self, "Duplicate",
                f"A request already exists for seat #{self.seat_data['seat_no']} "
                f"with proposed employee '{proposed}':\n{dup.id}"
            )
            return

        self.request = Request(
            requestor_name=name,
            requestor_email=email,
            department=self.department.currentText(),
            position=self.seat_data["seat_no"],
            current_employee=self.current_employee.text(),
            proposed_employee=proposed,
        )
        self.request.id = self.req_id.text()
        self.request.date = self.req_date.text()
        self.store.save(self.request)
        self.accept()
