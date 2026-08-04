import json
import os

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QBrush, QPen, QFont
from PySide6.QtWidgets import QGraphicsScene

from src.core.path_config import get_positions_path
from src.core.color_manager import DeptColorManager
from src.theme.theme import CELL_W, CELL_H, CELL_GAP, COLORS, SEAT_COLOR_FREE
from src.ui.room_item import RoomItem
from src.ui.seat_item import SeatItem


class FloorPlanScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.seats = []
        self.rooms = []
        self.seat_items = []
        self.selected_seat = None
        self.on_seat_selected = None
        self._occupancy_filter = "all"
        self._department_filter = None
        self.setBackgroundBrush(QBrush(QColor(COLORS["grid_bg"])))

    def load(self):
        self.clear()
        self.seat_items = []
        self.selected_seat = None
        path = get_positions_path()
        if not path or not os.path.exists(path):
            text = self.addText("positions.json not found", QFont("Segoe UI", 14))
            text.setPos(20, 20)
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.data = data

        rooms = data.get("rooms", [])
        for r in rooms:
            item = RoomItem(r)
            self.addItem(item)

        seats = data.get("seats", [])
        for s in seats:
            item = SeatItem(s)
            self.addItem(item)
            self.seat_items.append(item)

        rows = data["grid"]["rows"]
        cols = data["grid"]["cols"]
        w = (CELL_W + CELL_GAP) * cols
        h = (CELL_H + CELL_GAP) * rows
        self.setSceneRect(QRectF(0, 0, w + 20, h + 20))

    def seat_at(self, row, col):
        for item in self.seat_items:
            sd = item.seat_data
            if sd["row"] == row and sd["col"] == col:
                return sd
        return None

    def clear_selection(self):
        if self.selected_seat is not None:
            self.selected_seat.set_selected(False)
            self.selected_seat = None

    def select_seat_item(self, seat_item):
        self.clear_selection()
        seat_item.set_selected(True)
        self.selected_seat = seat_item

    def apply_filters(self, occupancy="all", department=None):
        self._occupancy_filter = occupancy
        self._department_filter = department
        for item in self.seat_items:
            matches_occupancy = (
                occupancy == "all" or
                (occupancy == "occupied" and item.occupied) or
                (occupancy == "vacant" and not item.occupied)
            )
            person = item.seat_data.get("person")
            seat_dept = person["department"] if person else None
            matches_dept = (
                department is None or department == "All Departments" or
                seat_dept == department
            )
            item.set_dimmed(not (matches_occupancy and matches_dept))

    def recolor_departments(self):
        """Recompute every seat color from the current department color config.

        In-place update: no scene rebuild, selection and filters preserved.
        ERROR seats keep their red diagnostic color.
        """
        for item in self.seat_items:
            seat_data = item.seat_data
            if seat_data.get("status") == "ERROR":
                item.color = "#ff0000"
            else:
                person = seat_data.get("person")
                dept = person["department"] if person else None
                item.color = DeptColorManager.get_color(dept, fallback=SEAT_COLOR_FREE)
            item.update()
