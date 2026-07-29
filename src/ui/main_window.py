from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow, QHBoxLayout, QVBoxLayout, QWidget,
    QLabel, QPushButton, QStatusBar, QMenu,
    QSplitter, QFrame, QGraphicsItem,
    QMessageBox, QToolBar,
)

from src.ui.floor_plan_scene import FloorPlanScene
from src.ui.floor_plan_view import FloorPlanView
from src.ui.request_panel import RequestPanel
from src.ui.request_dialog import RequestDialog
from src.core.request_store import RequestStore
from src.core.health_check import run_health_check
from src.core.path_config import get_requests_path, get_logs_path
from src.core.log_manager import LogManager
from src.core.exporter import export_to_pdf, export_to_xlsx
from src.theme.theme import COLORS


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SORTIS - Floor Plan v2")
        self.resize(1200, 800)

        self.log_manager = None
        requests_dir = get_requests_path()
        logs_dir = get_logs_path()
        if requests_dir:
            self.store = RequestStore(requests_dir)
        else:
            self.store = None
        if logs_dir:
            self.log_manager = LogManager(logs_dir)

        self._setup_menu()
        self._setup_central()
        self._setup_status_bar()
        self._run_health()
        self.scene.load()
        if hasattr(self, "request_panel"):
            self.request_panel.refresh()
            self._sync_departments()

    def _setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        refresh_action = QAction("Refresh Data", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self._refresh_data)
        file_menu.addAction(refresh_action)
        file_menu.addSeparator()
        export_pdf = QAction("Export Requests to PDF...", self)
        export_pdf.triggered.connect(self._export_pdf)
        file_menu.addAction(export_pdf)
        export_xlsx = QAction("Export Requests to Excel...", self)
        export_xlsx.triggered.connect(self._export_xlsx)
        file_menu.addAction(export_xlsx)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("View")
        zoom_in = QAction("Zoom In", self)
        zoom_in.setShortcut(QKeySequence("Ctrl++"))
        zoom_in.triggered.connect(self._zoom_in)
        view_menu.addAction(zoom_in)

        zoom_out = QAction("Zoom Out", self)
        zoom_out.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out.triggered.connect(self._zoom_out)
        view_menu.addAction(zoom_out)

        zoom_reset = QAction("Reset Zoom", self)
        zoom_reset.setShortcut(QKeySequence("Ctrl+0"))
        zoom_reset.triggered.connect(self._zoom_reset)
        view_menu.addAction(zoom_reset)

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_central(self):
        self.scene = FloorPlanScene(self)
        self.view = FloorPlanView(self.scene, self)
        self.view.setFrameShape(QFrame.Shape.NoFrame)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        seat_info_label = QLabel("Click a seat to view details")
        seat_info_label.setFont(QFont("Segoe UI", 10))
        seat_info_label.setStyleSheet("padding: 8px; background: #fff; border-bottom: 1px solid #ddd;")
        right_layout.addWidget(seat_info_label)
        self._seat_info = seat_info_label

        request_seat_btn = QPushButton("Request Change for Selected Seat")
        request_seat_btn.clicked.connect(self._request_for_selected)
        request_seat_btn.setEnabled(False)
        right_layout.addWidget(request_seat_btn)
        self._request_btn = request_seat_btn

        requests_dir = get_requests_path()
        if requests_dir:
            self.request_panel = RequestPanel(self.store, self)
            right_layout.addWidget(self.request_panel, stretch=1)
        else:
            placeholder = QLabel("Requests directory not found")
            right_layout.addWidget(placeholder, stretch=1)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.view)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

        self.scene.on_seat_selected = self._on_seat_selected
        if hasattr(self, "request_panel"):
            self.request_panel.on_filter_changed = self._on_filters_changed

    def _on_filters_changed(self, occupancy, department):
        dept = None if department == "All Departments" else department
        self.scene.apply_filters(occupancy, dept)
        self._push_counts()

    def _calculate_counts(self, department=None):
        occ = 0
        vac = 0
        for item in self.scene.seat_items:
            person = item.seat_data.get("person")
            seat_dept = person["department"] if person else None
            if department and department != "All Departments" and seat_dept != department:
                continue
            if item.occupied:
                occ += 1
            else:
                vac += 1
        return occ, vac

    def _push_counts(self):
        if not hasattr(self, "request_panel"):
            return
        dept = self.request_panel.dept_filter.currentText()
        occ, vac = self._calculate_counts(dept)
        self.request_panel.set_counts(occ + vac, occ, vac)

    def _sync_departments(self):
        data = getattr(self.scene, "data", {})
        depts = data.get("departments", [])
        if depts and hasattr(self, "request_panel"):
            self.request_panel.set_departments(depts)
        self._push_counts()

    def _setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._zoom_label = QLabel("100%")
        self.status_bar.addPermanentWidget(self._zoom_label)
        self.status_bar.showMessage("Ready")

    def _run_health(self):
        result = run_health_check()
        if result.all_pass:
            self.status_bar.showMessage(f"Health: {result.summary()}")
        else:
            for f in result.failures():
                self.status_bar.showMessage(f"Health: {f['error']}")
                break

    def _on_seat_selected(self, seat_item):
        sd = seat_item.seat_data
        person = sd.get("person")
        if person:
            self._seat_info.setText(
                f"<b>Seat #{sd['seat_no']}</b><br>"
                f"{person.get('name', '')}<br>"
                f"{person.get('department', '')} - {person.get('title', '')}"
            )
        else:
            self._seat_info.setText(
                f"<b>Seat #{sd['seat_no']}</b><br>"
                f"<i>Unassigned</i>"
            )
        self._request_btn.setEnabled(True)
        self._current_seat = seat_item

    def _request_for_selected(self):
        if not hasattr(self, "_current_seat") or self._current_seat is None:
            return
        seat_data = self._current_seat.seat_data
        data = getattr(self.scene, "data", {})
        departments = data.get("departments", [])
        dlg = RequestDialog(seat_data, departments, self.store, self)
        dlg.exec()
        if dlg.request:
            if self.log_manager:
                self.log_manager.log_event(
                    action="request_created",
                    request_id=dlg.request.id,
                    details={"position": seat_data["seat_no"]},
                )
            self.status_bar.showMessage(f"Request {dlg.request.id} created", 5000)
            self.request_panel.refresh()

    def _export_pdf(self):
        reqs = self.store.list_all()
        if not reqs:
            QMessageBox.information(self, "Export", "No requests to export")
            return
        export_to_pdf(reqs, self)
        self.status_bar.showMessage("PDF exported", 3000)

    def _export_xlsx(self):
        reqs = self.store.list_all()
        if not reqs:
            QMessageBox.information(self, "Export", "No requests to export")
            return
        export_to_xlsx(reqs, self)
        self.status_bar.showMessage("Excel exported", 3000)

    def _refresh_data(self):
        self.scene.load()
        self.view._apply_zoom()
        self.status_bar.showMessage("Data refreshed", 3000)
        if self.request_panel:
            self.request_panel.refresh()
            self._sync_departments()

    def _zoom_in(self):
        self.view.zoom_in()
        self._zoom_label.setText(f"{self.view.zoom_level}%")

    def _zoom_out(self):
        self.view.zoom_out()
        self._zoom_label.setText(f"{self.view.zoom_level}%")

    def _zoom_reset(self):
        self.view.zoom_reset()
        self._zoom_label.setText("100%")

    def _show_about(self):
        QMessageBox.about(self, "About SORTIS",
                          "SORTIS v2.0.0\n"
                          "Seating Organization & Request Tracking\n"
                          "Desktop Edition\n\n"
                          "Built with PySide6")
