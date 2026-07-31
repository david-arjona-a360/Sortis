"""
Role configuration manager.

Resolves the current Windows user's role from config/users_roles.json.

Fallback chain:
    1. config/users_roles.json  -> username -> role mapping
    2. default_role in the JSON -> role for unlisted users
    3. built-in fallback        -> "user" for everyone
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
            cls._users = {
                str(username).strip().lower(): str(role).strip().lower()
                for username, role in users.items()
                if str(role).strip()
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
    def role(cls, username=None):
        if cls._users is None:
            cls.load()
        username = (username or cls.current_user()).lower().strip()
        return cls._users.get(username, cls._default_role)

    @classmethod
    def is_admin(cls, username=None):
        return cls.role(username) == "admin"

    @classmethod
    def get_source(cls):
        if cls._users is None:
            cls.load()
        return cls._source
