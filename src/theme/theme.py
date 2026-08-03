SEAT_COLOR_FREE = "#e0e0e0"
SEAT_COLOR_OCCUPIED = "#4caf50"
SEAT_HOVER_COLOR = "#ffc107"
SEAT_SELECTED_COLOR = "#ff9800"
SEAT_BORDER = "#999"
TEXT_COLOR = "#333"

CELL_W = 42
CELL_H = 26
CELL_GAP = 1

COLORS = {
    "background": "#f5f5f5",
    "grid_bg": "#eee",
    "topbar_bg": "#1a237e",
    "topbar_text": "#ffffff",
    "dock_bg": "#ffffff",
    "dock_border": "#ddd",
}

# Centralized role styling. Key = internal role (never shown raw); the
# label is the friendly display text and bg/fg define the pill colors.
# Add future roles here (e.g. "superadmin") — no other code changes needed.
ROLE_STYLES = {
    "admin": {"label": "Administrator", "bg": "#dc1e28", "fg": "#ffffff"},
    "user": {"label": "User", "bg": "#3949ab", "fg": "#ffffff"},
    "superadmin": {"label": "Super Administrator", "bg": "#f9a825", "fg": "#333333"},
}

ROLE_FALLBACK_STYLE = {"label": "", "bg": "#757575", "fg": "#ffffff"}

# ── Dark dialog design system ──────────────────────────────────────────────
# Layered surfaces (Level 1 -> 5) and text hierarchy for all popup/dialog
# windows. Every fg/bg pair below meets WCAG AA (>= 4.5:1).
DIALOG_BG = "#1e1e1e"            # L1 dialog background
PANEL_BG = "#252526"             # L2 panel / sections / table header
CARD_BG = "#2d2d30"              # L3 card background (details section)
SELECT_BG = "#094771"            # L4 selected row / selected item
HOVER_BG = "#2a2d2e"             # L4 hover
BORDER_COLOR = "#3c3c3c"
INPUT_BG = "#3c3c3c"
INPUT_READONLY_BG = "#2a2a2a"

TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#d0d0d0"
TEXT_MUTED = "#bdbdbd"
TEXT_DISABLED = "#8a8a8a"

ACCENT = "#0e639c"               # primary action
ACCENT_HOVER = "#1177bb"
DANGER = "#c62828"               # destructive action
DANGER_HOVER = "#d32f2f"

# status key -> (background, foreground). Used for status pills in tables.
STATUS_STYLES = {
    "pending": ("#f9a825", "#1a1a1a"),
    "completed": ("#2e7d32", "#ffffff"),
    "cancelled": ("#757575", "#ffffff"),
}
