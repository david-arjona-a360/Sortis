from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPen
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem

from src.theme.theme import (
    CELL_W, CELL_H, CELL_GAP, DEPT_COLORS,
    SEAT_COLOR_FREE, SEAT_HOVER_COLOR, SEAT_SELECTED_COLOR,
)


class SeatItem(QGraphicsRectItem):
    def __init__(self, seat_data, parent=None):
        w = CELL_W + CELL_GAP
        h = CELL_H + CELL_GAP
        row = seat_data["row"]
        col = seat_data["col"]
        x = (col - 1) * w
        y = (row - 1) * h
        super().__init__(QRectF(x, y, CELL_W, CELL_H))

        self.seat_data = seat_data
        self._selected = False
        self._hovered = False

        person = seat_data.get("person")
        self.occupied = person is not None
        dept = person["department"] if person else None
        self.color = DEPT_COLORS.get(dept, SEAT_COLOR_FREE) if dept else SEAT_COLOR_FREE
        self.setBrush(QBrush(QColor(self.color)))
        self.setPen(QPen(QColor("#000"), 0))
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        label = QGraphicsTextItem(seat_data["seat_no"], self)
        label.setDefaultTextColor(QColor("#333" if not self.occupied else "#fff"))
        font = QFont("Segoe UI", 7, QFont.Weight.Bold)
        label.setFont(font)
        lr = label.boundingRect()
        label.setPos(x + (CELL_W - lr.width()) / 2, y + (CELL_H - lr.height()) / 2)
        self._label = label

    def paint(self, painter, option, widget=None):
        color = QColor(self.color)
        if self._hovered:
            color = QColor(SEAT_HOVER_COLOR)
        if self._selected:
            color = QColor(SEAT_SELECTED_COLOR)
        painter.setBrush(QBrush(color))
        border = QColor("#fff" if self.occupied else "#999")
        painter.setPen(QPen(border, 0.5))
        painter.drawRoundedRect(self.rect(), 2, 2)

        if self.occupied and not self._hovered and not self._selected:
            painter.setBrush(QBrush(QColor("#4caf50")))
            painter.setPen(Qt.PenStyle.NoPen)
            dot_rect = self.rect().adjusted(2, 2, -2, -2)
            painter.drawEllipse(dot_rect.topRight() + dot_rect.bottomRight(), 2, 2)

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def set_selected(self, selected):
        self._selected = selected
        self.update()
