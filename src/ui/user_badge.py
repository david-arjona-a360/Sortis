from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QToolButton, QMenu,
)

from src.core.auth_manager import AuthManager
from src.theme.theme import COLORS, ROLE_STYLES, ROLE_FALLBACK_STYLE

_BADGE_BG = COLORS["topbar_bg"]
_BADGE_FG = COLORS["topbar_text"]
_BADGE_MUTED = "#b6bfd9"
_MAX_NAME_CHARS = 26
_MAX_USERNAME_CHARS = 18


def _initials(display_name, username):
    parts = [p for p in display_name.replace(".", " ").split() if p]
    if not parts:
        chars = (username or "?").strip()[:2] or "?"
        return chars.upper()
    first = parts[0][0]
    second = parts[1][0] if len(parts) > 1 else ""
    return (first + second).upper() or "?"


def _elide(text, max_chars):
    return text if len(text) <= max_chars else text[: max_chars - 1].rstrip() + "\u2026"


class RolePill(QLabel):
    def __init__(self, role, parent=None):
        super().__init__(parent)
        style = ROLE_STYLES.get(role, ROLE_FALLBACK_STYLE)
        label = style["label"] or role.replace("_", " ").title()
        self.setText(label)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(15)
        self.setStyleSheet(
            f"background-color: {style['bg']}; color: {style['fg']};"
            "border-radius: 8px; padding: 0 8px;"
            "font-family: 'Segoe UI'; font-size: 9px; font-weight: 600;"
        )


class UserBadge(QWidget):
    """Top-right identity indicator.

    Shows avatar initials, display name (username), and a colored role pill.
    The dropdown menu is an extension point for future actions
    (Profile, Preferences, My Requests, Admin Panel, Diagnostics, About).
    """

    def __init__(self, user_info, parent=None):
        super().__init__(parent)
        self.user_info = user_info or {}
        self._menu = QMenu(self)

        display_name = self.user_info.get("display_name") or AuthManager.display_name()
        username = self.user_info.get("username") or AuthManager.current_user()
        role = self.user_info.get("role") or "user"

        self.setObjectName("UserBadge")
        self.setStyleSheet(f"QWidget#UserBadge {{ background-color: {_BADGE_BG}; border-radius: 12px; }}")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(8, 2, 3, 2)
        outer.setSpacing(6)

        self.avatar = QLabel(_initials(display_name, username))
        self.avatar.setObjectName("UserBadgeAvatar")
        self.avatar.setFixedSize(20, 20)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setStyleSheet(
            f"QLabel#UserBadgeAvatar {{ background-color: {_BADGE_FG};"
            f"color: {_BADGE_BG}; border-radius: 10px;"
            "font-family: 'Segoe UI'; font-size: 8px; font-weight: 700; }"
        )

        name_line = f"<b>{_elide(display_name, _MAX_NAME_CHARS)}</b>"
        if username and username.lower() != display_name.lower():
            name_line += (
                " <span style='color:%s;font-size:7pt'>(%s)</span>"
                % (_BADGE_MUTED, _elide(username, _MAX_USERNAME_CHARS))
            )
        self.name_label = QLabel(name_line)
        self.name_label.setTextFormat(Qt.TextFormat.RichText)
        self.name_label.setStyleSheet(
            f"color: {_BADGE_FG}; font-family: 'Segoe UI'; font-size: 10px;"
        )

        self.pill = RolePill(role)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(1)
        text_col.addWidget(self.name_label)
        text_col.addWidget(self.pill)

        self.menu_button = QToolButton(self)
        self.menu_button.setArrowType(Qt.ArrowType.DownArrow)
        self.menu_button.setAutoRaise(True)
        self.menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu_button.setMenu(self._menu)
        self.menu_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_button.setStyleSheet(
            f"QToolButton {{ color: {_BADGE_FG}; background: transparent; border: none; padding: 0 2px; }}"
            "QToolButton::menu-indicator { image: none; }"
        )

        outer.addWidget(self.avatar)
        outer.addLayout(text_col)
        outer.addWidget(self.menu_button)

        self.setToolTip(self._build_tooltip(display_name, username, role))

    def _build_tooltip(self, display_name, username, role):
        style = ROLE_STYLES.get(role, ROLE_FALLBACK_STYLE)
        role_label = style["label"] or role.replace("_", " ").title()
        lines = [f"<b>{display_name}</b> ({username})", f"Role: {role_label}"]
        for key, label in (("email", "Email"), ("department", "Department"),
                           ("location", "Location")):
            if self.user_info.get(key):
                lines.append(f"{label}: {self.user_info[key]}")
        return "<br>".join(lines)

    def add_menu_action(self, text, slot):
        action = self._menu.addAction(text)
        action.triggered.connect(slot)
        return action
