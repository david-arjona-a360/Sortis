import os
import json
from datetime import datetime, timezone
from .file_utils import atomic_write_json, read_json_file, ensure_directory


class RequestStore:
    def __init__(self, requests_dir):
        self.requests_dir = requests_dir

    def _ensure_dir(self):
        ensure_directory(self.requests_dir)

    def _filename(self, request_id):
        return f"{request_id}.json"

    def _path(self, request_id):
        return os.path.join(self.requests_dir, self._filename(request_id))

    def save(self, request):
        self._ensure_dir()
        atomic_write_json(self.requests_dir, self._filename(request.id), request.to_dict())

    def get(self, request_id):
        path = self._path(request_id)
        if not os.path.exists(path):
            return None
        data = read_json_file(path)
        from ..models.request import Request
        return Request.from_dict(data)

    def list_all(self):
        self._ensure_dir()
        if not os.path.isdir(self.requests_dir):
            return []
        files = []
        for f in os.listdir(self.requests_dir):
            if f.endswith(".json") and not f.startswith("."):
                files.append(f)
        files.sort(reverse=True)
        result = []
        for f in files:
            path = os.path.join(self.requests_dir, f)
            try:
                data = read_json_file(path)
                from ..models.request import Request
                result.append(Request.from_dict(data))
            except (json.JSONDecodeError, IOError, KeyError):
                continue
        return result

    def delete(self, request_id):
        path = self._path(request_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def set_status(self, request_id, status, by=None):
        from ..models.request import REQUEST_STATUSES, STATUS_PENDING
        path = self._path(request_id)
        if not os.path.exists(path) or status not in REQUEST_STATUSES:
            return False
        data = read_json_file(path)
        data["status"] = status
        if status == STATUS_PENDING:
            data["resolved_at"] = ""
            data["resolved_by"] = ""
        else:
            data["resolved_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            data["resolved_by"] = by or ""
        atomic_write_json(self.requests_dir, self._filename(request_id), data)
        return True

    def count(self):
        self._ensure_dir()
        if not os.path.isdir(self.requests_dir):
            return 0
        return sum(
            1 for f in os.listdir(self.requests_dir)
            if f.endswith(".json") and not f.startswith(".")
        )

    def find_conflict_files(self):
        self._ensure_dir()
        if not os.path.isdir(self.requests_dir):
            return []
        return [
            f for f in os.listdir(self.requests_dir)
            if "_conflict" in f
        ]
