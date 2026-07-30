from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget,
    QLabel, QStatusBar, QMenu,
    QSplitter, QFrame, QMessageBox,
)

from src.ui.floor_plan_scene import FloorPlanScene
from src.ui.floor_plan_view import FloorPlanView
from src.ui.filter_bar import FilterBar
from src.ui.seat_info_panel import SeatInfoPanel
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

        self.filter_bar = FilterBar()
        self.filter_bar.filter_changed.connect(self._on_filters_changed)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addWidget(self.filter_bar)
        left_layout.addWidget(self.view, stretch=1)

        self.seat_info_panel = SeatInfoPanel()
        self.seat_info_panel.request_clicked.connect(self._request_for_selected)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(self.seat_info_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

        self.scene.on_seat_selected = self._on_seat_selected

    def _on_filters_changed(self, occupancy, department):
        dept = None if department == "All Departments" else department
        self.scene.apply_filters(occupancy, dept)
        self._push_counts()
        occ, vac = self._calculate_counts(self.filter_bar.current_department)
        self.seat_info_panel.set_stats(occ + vac, occ, vac)

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
        dept = self.filter_bar.current_department
        occ, vac = self._calculate_counts(dept)
        self.filter_bar.set_counts(occ + vac, occ, vac)

    def _sync_departments(self):
        data = getattr(self.scene, "data", {})
        depts = data.get("departments", [])
        if depts:
            self.filter_bar.set_departments(depts)
        self._push_counts()
        occ, vac = self._calculate_counts("All Departments")
        self.seat_info_panel.set_stats(occ + vac, occ, vac)

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
        self.seat_info_panel.show_seat_info(seat_item.seat_data)
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
        self._sync_departments()
        self.seat_info_panel.clear_selection()

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
