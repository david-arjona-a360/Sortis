from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QWheelEvent, QMouseEvent, QPainter
from PySide6.QtWidgets import QGraphicsView


class FloorPlanView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHints(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._zoom = 100
        self._min_zoom = 20
        self._max_zoom = 400
        self._panning = False
        self._last_pan = QPointF()

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        if delta > 0:
            self._zoom = min(self._max_zoom, self._zoom + 10)
        else:
            self._zoom = max(self._min_zoom, self._zoom - 10)
        self._apply_zoom()

    def _apply_zoom(self):
        scale = self._zoom / 100.0
        transform = self.transform()
        transform.reset()
        transform.scale(scale, scale)
        self.setTransform(transform)

    def zoom_in(self):
        self._zoom = min(self._max_zoom, self._zoom + 10)
        self._apply_zoom()

    def zoom_out(self):
        self._zoom = max(self._min_zoom, self._zoom - 10)
        self._apply_zoom()

    def zoom_reset(self):
        self._zoom = 100
        self._apply_zoom()

    @property
    def zoom_level(self):
        return self._zoom
