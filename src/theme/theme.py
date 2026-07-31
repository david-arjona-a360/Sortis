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
