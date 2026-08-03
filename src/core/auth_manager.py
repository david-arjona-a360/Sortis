"""
Role configuration manager.

Resolves the current Windows user's role from config/users_roles.json.

Fallback chain:
    1. config/users_roles.json  -> username -> {role, display_name, ...}
    2. default_role in the JSON -> role for unlisted users
    3. built-in fallback        -> "user" for everyone

Schema compatibility:
    v1 (legacy):  "users": {"username": "admin"}
    v2 (current): "users": {"username": {"role": "admin", "display_name": "..."}}
Both are accepted; future keys (email, department, avatar, location) are
forward-compatible attributes of the per-user dict.
"""

import json
import os
import sys


def _app_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_users_roles_path():
    return os.path.join(_app_base_dir(), "config", "users_roles.json")


def _prettify_username(username):
    parts = [p for p in username.replace(".", " ").replace("_", " ").strip().split()]
    return " ".join(p.capitalize() for p in parts) or username


def _coerce_entry(username, value, default_role):
    """Accept both legacy (str role) and current (dict) formats."""
    if isinstance(value, dict):
        entry = dict(value)
        role = str(entry.get("role") or default_role).strip().lower()
        entry["role"] = role
        if not entry.get("display_name"):
            entry["display_name"] = _prettify_username(username)
        return entry
    role = str(value or default_role).strip().lower()
    return {"role": role, "display_name": _prettify_username(username)}


class AuthManager:
    _users = None
    _default_role = None
    _source = None

    @classmethod
    def load(cls, path=None):
        cls._users = {}
        cls._default_role = "user"
        cls._source = "built-in fallback"

        cfg_path = path or get_users_roles_path()
        if not cfg_path or not os.path.exists(cfg_path):
            return False

        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            return False

        if not isinstance(data, dict):
            return False

        users = data.get("users")
        if isinstance(users, dict):
            default_role = cls._default_role
            cls._users = {
                str(username).strip().lower(): _coerce_entry(
                    str(username).strip(), value, default_role
                )
                for username, value in users.items()
                if value
            }
            if cls._users:
                cls._source = cfg_path

        default_role = data.get("default_role")
        if isinstance(default_role, str) and default_role.strip():
            cls._default_role = default_role.strip().lower()

        return True

    @staticmethod
    def current_user():
        return (os.environ.get("USERNAME") or os.environ.get("USER") or "").lower().strip()

    @classmethod
    def _entry(cls, username=None):
        if cls._users is None:
            cls.load()
        username = (username or cls.current_user()).lower().strip()
        return cls._users.get(username)

    @classmethod
    def role(cls, username=None):
        entry = cls._entry(username)
        return entry["role"] if entry else cls._default_role

    @classmethod
    def display_name(cls, username=None):
        entry = cls._entry(username)
        if entry and entry.get("display_name"):
            return entry["display_name"]
        return _prettify_username(username or cls.current_user())

    @classmethod
    def is_admin(cls, username=None):
        return cls.role(username) == "admin"

    @classmethod
    def get_user_info(cls, username=None):
        entry = cls._entry(username) or {}
        username = (username or cls.current_user()).lower().strip()
        info = {
            "username": username,
            "role": entry.get("role", cls._default_role),
            "display_name": entry.get("display_name")
            or _prettify_username(username),
        }
        for key in ("email", "department", "location", "avatar"):
            if entry.get(key):
                info[key] = entry[key]
        return info

    @classmethod
    def get_source(cls):
        if cls._users is None:
            cls.load()
        return cls._source
