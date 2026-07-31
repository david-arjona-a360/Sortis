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
