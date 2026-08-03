"""Reusable dark design system for all SORTIS dialog/popup windows.

Apply once per dialog with ``apply_dialog_theme(dialog)``. The stylesheet is
self-contained (no dependence on the OS palette), so dialogs render with the
same dark, high-contrast look on any system.

Button hierarchy is expressed with the ``role`` property:
    primary   -> accent filled   [Mark Completed]
    danger    -> red filled      [Mark Cancelled]
    (default) -> neutral         [Export, Refresh, Close]
"""

from PySide6.QtWidgets import QWidget

from src.theme.theme import (
    DIALOG_BG, PANEL_BG, CARD_BG, SELECT_BG, HOVER_BG,
    BORDER_COLOR, INPUT_BG, INPUT_READONLY_BG,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_DISABLED,
    ACCENT, ACCENT_HOVER, DANGER, DANGER_HOVER,
)

DIALOG_QSS = f"""
QDialog {{
    background-color: {DIALOG_BG};
    color: {TEXT_SECONDARY};
}}
QLabel {{ background: transparent; color: {TEXT_SECONDARY}; }}
QLabel[role="title"] {{ color: {TEXT_PRIMARY}; font-size: 13px; font-weight: 600; }}
QLabel[role="section"] {{ color: {TEXT_PRIMARY}; font-size: 11px; font-weight: 600; }}

QFrame#cardFrame {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
}}

QLineEdit {{
    background-color: {INPUT_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 4px 8px;
}}
QLineEdit:read-only {{
    background-color: {INPUT_READONLY_BG};
    color: {TEXT_MUTED};
}}

QComboBox {{
    background-color: {INPUT_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 4px 8px;
}}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox QAbstractItemView {{
    background-color: {PANEL_BG};
    color: {TEXT_PRIMARY};
    selection-background-color: {SELECT_BG};
    selection-color: {TEXT_PRIMARY};
}}

QTableWidget {{
    background-color: {DIALOG_BG};
    alternate-background-color: {PANEL_BG};
    color: {TEXT_SECONDARY};
    gridline-color: {BORDER_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    selection-background-color: {SELECT_BG};
    selection-color: {TEXT_PRIMARY};
}}
QTableWidget::item {{ padding: 4px 6px; }}
QTableWidget::item:hover {{ background-color: {HOVER_BG}; }}
QHeaderView::section {{
    background-color: {PANEL_BG};
    color: {TEXT_PRIMARY};
    border: none;
    border-bottom: 2px solid {BORDER_COLOR};
    padding: 6px 8px;
    font-weight: 600;
}}

QPushButton {{
    background-color: {PANEL_BG};
    color: {TEXT_SECONDARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 6px 14px;
}}
QPushButton:hover {{ background-color: {HOVER_BG}; color: {TEXT_PRIMARY}; }}
QPushButton:disabled {{
    color: {TEXT_DISABLED};
    background-color: {DIALOG_BG};
    border-color: {BORDER_COLOR};
}}

QPushButton[role="primary"] {{
    background-color: {ACCENT};
    color: #ffffff;
    border: none;
    font-weight: 600;
}}
QPushButton[role="primary"]:hover {{ background-color: {ACCENT_HOVER}; }}
QPushButton[role="primary"]:disabled {{ background-color: {ACCENT}; color: {TEXT_DISABLED}; }}

QPushButton[role="danger"] {{
    background-color: {DANGER};
    color: #ffffff;
    border: none;
    font-weight: 600;
}}
QPushButton[role="danger"]:hover {{ background-color: {DANGER_HOVER}; }}
QPushButton[role="danger"]:disabled {{ background-color: {DANGER}; color: {TEXT_DISABLED}; }}
"""


def apply_dialog_theme(widget: QWidget):
    """Apply the dark dialog design system to *widget* and its children."""
    widget.setStyleSheet(widget.styleSheet() + DIALOG_QSS)


def style_button(button, role=None):
    """Assign a hierarchy role to a button: 'primary', 'danger' or None."""
    button.setProperty("role", role or "")
    button.style().unpolish(button)
    button.style().polish(button)
    button.update()
