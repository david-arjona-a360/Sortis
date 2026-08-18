from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush, QColor, QFont, QPen
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QMenu

from src.theme.theme import CELL_W, CELL_H, CELL_GAP, TEXT_COLOR

ROOM_COLORS = {
    "COMEDOR": "#f5c6cb",
    "ARCHIVE": "#d6d8db",
    "CUARTO DE IT": "#e78c92",
    "BAÑO DE MUJERES": "#bfc1c5",
    "BAÑO DE HOMBRES": "#bfc1c5",
    "LOCKERS": "#e8e8ec",
    "SALA DE ENTRENAMIENTO": "#dc1e28",
    "SALA DE REUNIONES": "#a8323b",
    "RECEPCION": "#6c757d",
    "CUARTO ELECTRICO": "#d6d8db",
    "CUARTO DE A/C": "#d6d8db",
    "OFICINA DE IT": "#e78c92",
    "DEPOSITO IT": "#e78c92",
    "WAR ROOM": "#dc1e28",
    "OFICINA GERENCIA": "#50505a",
    "HR162": "#a8323b",
    "Supervisor": "#50505a",
}


def _room_color(name):
    if not name:
        return "#e0e0e0"
    for key, color in ROOM_COLORS.items():
        if key in name:
            return color
    return "#e0e0e0"


class RoomItem(QGraphicsRectItem):
    def __init__(self, room_data, parent=None):
        w = CELL_W + CELL_GAP
        h = CELL_H + CELL_GAP
        min_r = room_data["min_row"]
        min_c = room_data["min_col"]
        max_r = room_data["max_row"]
        max_c = room_data["max_col"]
        x = (min_c - 1) * w
        y = (min_r - 1) * h
        rw = (max_c - min_c + 1) * w - CELL_GAP
        rh = (max_r - min_r + 1) * h - CELL_GAP
        super().__init__(QRectF(x, y, rw, rh))
        self.room_data = room_data
        color = _room_color(room_data.get("name", ""))
        self.setBrush(QBrush(QColor(color)))
        self.setPen(QPen(QColor("#000"), 0))
        self.setZValue(-1)

        name = room_data.get("name", "").strip()
        self._room_text = None
        if name:
            text = QGraphicsTextItem(name, self)
            text.setDefaultTextColor(QColor(TEXT_COLOR))
            font = QFont("Segoe UI", 8, QFont.Weight.Bold)
            text.setFont(font)
            tr = text.boundingRect()
            if rw < tr.width() + 10:
                font.setPointSize(6)
                text.setFont(font)
                tr = text.boundingRect()
            text.setPos(x + (rw - tr.width()) / 2, y + (rh - tr.height()) / 2)
            text.setZValue(0)
            self._room_text = text

        self.setAcceptedMouseButtons(Qt.MouseButton.RightButton)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            scene = self.scene()
            if scene and hasattr(scene, "on_room_right_clicked") and scene.on_room_right_clicked:
                scene.on_room_right_clicked(self.room_data)
        super().mousePressEvent(event)
