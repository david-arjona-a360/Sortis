import uuid
from datetime import datetime, timezone


STATUS_PENDING = "pending"
STATUS_COMPLETED = "completed"
STATUS_CANCELLED = "cancelled"
REQUEST_STATUSES = (STATUS_PENDING, STATUS_COMPLETED, STATUS_CANCELLED)


class Request:
    def __init__(self, requestor_name, requestor_email, department,
                 position, current_employee, proposed_employee):
        now = datetime.now(timezone.utc)
        date_part = now.strftime("%Y%m%d")
        unique_part = uuid.uuid4().hex[:6].upper()
        self.id = f"REQ-{date_part}-{unique_part}"
        self.date = now.strftime("%Y-%m-%d")
        self.requestor_name = requestor_name
        self.requestor_email = requestor_email
        self.department = department
        self.position = position
        self.current_employee = current_employee or ""
        self.proposed_employee = proposed_employee
        self.created_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.version = 2
        self.status = STATUS_PENDING
        self.resolved_at = ""
        self.resolved_by = ""

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
            "requestor_name": self.requestor_name,
            "requestor_email": self.requestor_email,
            "department": self.department,
            "position": self.position,
            "current_employee": self.current_employee,
            "proposed_employee": self.proposed_employee,
            "created_at": self.created_at,
            "status": self.status,
            "resolved_at": self.resolved_at,
            "resolved_by": self.resolved_by,
            "version": self.version,
        }

    @staticmethod
    def from_dict(data):
        r = Request(
            requestor_name=data["requestor_name"],
            requestor_email=data["requestor_email"],
            department=data["department"],
            position=data["position"],
            current_employee=data.get("current_employee", ""),
            proposed_employee=data["proposed_employee"],
        )
        r.id = data["id"]
        r.date = data["date"]
        r.created_at = data.get("created_at", data["date"] + "T00:00:00Z")
        r.version = data.get("version", 1)
        r.status = data.get("status", STATUS_PENDING)
        r.resolved_at = data.get("resolved_at", "")
        r.resolved_by = data.get("resolved_by", "")
        return r
