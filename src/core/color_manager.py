"""
Department color configuration manager.

Loads department->color mappings from config/dept_colors.json.

Priority / fallback chain:
    1. config/dept_colors.json        -> configured value
    2. default_color in the JSON      -> configured default
    3. _FALLBACK_DEPT_COLORS (below)  -> hardcoded fallback
    4. _FALLBACK_DEFAULT_COLOR        -> final fallback
"""

import json
import os
import re
import sys

from src.core.file_utils import atomic_write_json
from src.core.path_config import get_shared_dept_colors_path
from src.theme.theme import SEAT_COLOR_FREE

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

# Hardcoded fallback used when the JSON configuration is missing/corrupt.
# Kept here (not in theme.py) so theme.py stays pure UI styling.
_FALLBACK_DEPT_COLORS = {
    "ADM": "#50505a",
    "Finance": "#50505a",
    "FS": "#bfc1c5",
    "IBC": "#d6d8db",
    "IT": "#dc1e28",
    "POCPro": "#d6d8db",
    "ProVest": "#f5c6cb",
    "ProVest F&A": "#e78c92",
    "Title": "#f5c6cb",
    "Trainer": "#d6d8db",
    "VS360": "#a8323b",
}

_FALLBACK_DEFAULT_COLOR = SEAT_COLOR_FREE


def _app_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_dept_colors_path():
    """Resolve the dept colors config file.

    Priority:
        1. Shared OneDrive config (FLOOR PLAN/dept_colors.json) - source of truth.
           Admin writes here so every installation reads the same colors.
        2. Local config next to the executable - fallback when the shared
           folder is not mounted (offline) or not yet created.
    """
    shared = get_shared_dept_colors_path()
    if shared and os.path.exists(shared):
        return shared
    return os.path.join(_app_base_dir(), "config", "dept_colors.json")


class DeptColorManager:
    _colors = None
    _default = None
    _source = None

    @classmethod
    def load(cls, path=None):
        cls._colors = dict(_FALLBACK_DEPT_COLORS)
        cls._default = _FALLBACK_DEFAULT_COLOR
        cls._source = "built-in fallback"

        cfg_path = path or get_dept_colors_path()
        if not cfg_path or not os.path.exists(cfg_path):
            return False

        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            return False

        if not isinstance(data, dict):
            return False

        depts = data.get("departments")
        if not isinstance(depts, dict):
            return False

        valid = {}
        for dept, color in depts.items():
            if isinstance(color, str) and _HEX_RE.match(color):
                valid[dept] = color.upper()

        if valid:
            cls._colors = valid
            cls._source = cfg_path

        default = data.get("default_color")
        if isinstance(default, str) and _HEX_RE.match(default):
            cls._default = default.upper()

        return bool(valid)

    @classmethod
    def get_color(cls, department, fallback=None):
        if cls._colors is None:
            cls.load()
        if department and department in cls._colors:
            return cls._colors[department]
        return fallback or cls._default

    @classmethod
    def get_all_colors(cls):
        if cls._colors is None:
            cls.load()
        return dict(cls._colors)

    @classmethod
    def get_default_color(cls):
        if cls._colors is None:
            cls.load()
        return cls._default

    @classmethod
    def get_source(cls):
        if cls._colors is None:
            cls.load()
        return cls._source

    @classmethod
    def _build_config(cls, departments=None, default_color=None):
        depts = departments if departments is not None else cls._colors
        default = default_color if default_color is not None else cls._default
        return {
            "version": 1,
            "default_color": str(default).upper(),
            "departments": {
                str(name).strip(): str(color).upper()
                for name, color in (depts or {}).items()
            },
        }

    @classmethod
    def save(cls, departments=None, default_color=None, path=None):
        """Persist colors atomically to the config file, then reload.

        Writes to the shared OneDrive config by default (single source of
        truth). Falls back to the local config only when the shared path
        cannot be resolved/created (e.g. OneDrive not mounted).
        """
        data = cls._build_config(departments, default_color)
        cfg_path = path or get_dept_colors_path()
        directory = os.path.dirname(cfg_path)
        os.makedirs(directory, exist_ok=True)
        atomic_write_json(directory, os.path.basename(cfg_path), data)
        return cls.load(cfg_path)

    @classmethod
    def update_department(cls, department, color, path=None):
        """Set or add a department color, persisting immediately."""
        if cls._colors is None:
            cls.load()
        depts = dict(cls._colors)
        depts[str(department).strip()] = str(color).upper()
        return cls.save(depts, path=path)

    @classmethod
    def set_default(cls, color, path=None):
        """Set the default color for unlisted departments, persisting."""
        if cls._colors is None:
            cls.load()
        return cls.save(cls._colors, str(color).upper(), path=path)

    @classmethod
    def restore_defaults(cls, path=None):
        """Restore the built-in fallback palette, persisting."""
        return cls.save(_FALLBACK_DEPT_COLORS, _FALLBACK_DEFAULT_COLOR, path=path)
