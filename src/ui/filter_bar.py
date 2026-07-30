from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QComboBox, QLabel,
)

_BTN_ACTIVE = """
    QPushButton {
        background: #1a237e; color: #fff; font-weight: 700;
        border: 1px solid #1a237e; padding: 5px 10px; font-size: 11px;
    }
"""
_BTN_INACTIVE = """
    QPushButton {
        background: #e0e0e0; color: #555; font-weight: 500;
        border: 1px solid #ccc; padding: 5px 10px; font-size: 11px;
    }
    QPushButton:hover { background: #d0d0d0; }
"""


class FilterBar(QWidget):
    filter_changed = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._occupancy = "all"
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        seg_layout = QHBoxLayout()
        seg_layout.setContentsMargins(0, 0, 0, 0)
        seg_layout.setSpacing(0)
        self.btn_all = QPushButton("All")
        self.btn_occupied = QPushButton("Occupied")
        self.btn_vacant = QPushButton("Vacant")
        self.btn_all._occ_mode = "all"
        self.btn_occupied._occ_mode = "occupied"
        self.btn_vacant._occ_mode = "vacant"
        for b in (self.btn_all, self.btn_occupied, self.btn_vacant):
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(_BTN_INACTIVE)
            seg_layout.addWidget(b)
        self._filter_btns = [self.btn_all, self.btn_occupied, self.btn_vacant]
        self.btn_all.setChecked(True)
        self.btn_all.setStyleSheet(_BTN_ACTIVE)
        self.btn_all.clicked.connect(lambda: self._set_occupancy("all"))
        self.btn_occupied.clicked.connect(lambda: self._set_occupancy("occupied"))
        self.btn_vacant.clicked.connect(lambda: self._set_occupancy("vacant"))
        layout.addLayout(seg_layout)
        layout.addSpacing(12)
        dept_label = QLabel("Department:")
        dept_label.setFont(QFont("Segoe UI", 9))
        layout.addWidget(dept_label)
        self.dept_filter = QComboBox()
        self.dept_filter.addItem("All Departments")
        self.dept_filter.currentTextChanged.connect(self._emit_filter)
        layout.addWidget(self.dept_filter)
        layout.addStretch()

    def _set_occupancy(self, value):
        self._occupancy = value
        for b in self._filter_btns:
            active = getattr(b, "_occ_mode", None) == value
            b.setChecked(active)
            b.setStyleSheet(_BTN_ACTIVE if active else _BTN_INACTIVE)
        self._emit_filter()

    def set_counts(self, total, occupied, vacant):
        for b in self._filter_btns:
            mode = getattr(b, "_occ_mode", None)
            if mode == "all":
                b.setText(f"All ({total})")
            elif mode == "occupied":
                b.setText(f"Occupied ({occupied})")
            elif mode == "vacant":
                b.setText(f"Vacant ({vacant})")

    def set_departments(self, dept_list):
        current = self.dept_filter.currentText()
        self.dept_filter.blockSignals(True)
        self.dept_filter.clear()
        self.dept_filter.addItem("All Departments")
        for d in sorted(dept_list):
            self.dept_filter.addItem(d)
        idx = self.dept_filter.findText(current)
        if idx >= 0:
            self.dept_filter.setCurrentIndex(idx)
        self.dept_filter.blockSignals(False)

    def _emit_filter(self):
        self.filter_changed.emit(self._occupancy, self.dept_filter.currentText())

    @property
    def current_department(self):
        return self.dept_filter.currentText()

    @property
    def current_occupancy(self):
        return self._occupancy
