import json
import os
import logging
from datetime import datetime, timezone, timedelta

_EVENTS_LOG = "events.log"
_MAX_LOG_AGE_DAYS = 7


class LogManager:
    def __init__(self, log_dir):
        self.log_dir = log_dir
        self._events_path = os.path.join(log_dir, _EVENTS_LOG) if log_dir else None
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            self._rotate_if_needed()

    def _rotate_if_needed(self):
        if not self._events_path or not os.path.exists(self._events_path):
            return
        mtime = datetime.fromtimestamp(os.path.getmtime(self._events_path))
        if datetime.now() - mtime > timedelta(days=_MAX_LOG_AGE_DAYS):
            base, ext = os.path.splitext(self._events_path)
            old_name = f"{base}_{mtime.strftime('%Y%m%d')}{ext}"
            os.rename(self._events_path, old_name)

    def log_event(self, action, user="", request_id="", details=None):
        entry = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "user": user,
            "action": action,
            "request_id": request_id,
        }
        if details:
            entry["details"] = details
        line = json.dumps(entry, ensure_ascii=False)
        if self._events_path:
            try:
                with open(self._events_path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except (IOError, OSError) as e:
                logging.getLogger("sortis.log").warning("Failed to write log: %s", e)
