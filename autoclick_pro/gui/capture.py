from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QPushButton

from autoclick_pro.util.screen import grab_screen, grab_region


class CaptureDialog(QDialog):
    """
    Fullscreen screenshot preview with drag-to-select ROI.
    Saves ROI to templates directory.
    """

    def __init__(self, parent=None, templates_dir: Path = Path("templates")) -> None:
        super().__init__(parent)
        self.setWindowTitle("Capture Screen Object")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setWindowState(self.windowState() | Qt.WindowState.WindowFullScreen)

        self.templates_dir = templates_dir
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        self._start: Optional[QPoint] = None
        self._end: Optional[QPoint] = None

        v = QVBoxLayout(self)
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(self.label)

        self.btn_save = QPushButton("Save Selection")
        v.addWidget(self.btn_save)
        self.btn_save.clicked.connect(self._save_selection)

        # Load current screen
        self.screen_path = grab_screen()
        self.pixmap = QPixmap(str(self.screen_path))
        self.label.setPixmap(self.pixmap)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.position().toPoint()
            self._end = self._start

    def mouseMoveEvent(self, event) -> None:
        if self._start is not None:
            self._end = event.position().toPoint()
            self._update_overlay()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._end = event.position().toPoint()
            self._update_overlay()

    def _update_overlay(self) -> None:
        pm = QPixmap(str(self.screen_path))
        if self._start and self._end:
            rect = QRect(self._start, self._end).normalized()
            painter = QPainter(pm)
            painter.setPen(QColor(80, 180, 255))
            # Semi-transparent fill for selection
            painter.fillRect(rect, QColor(80, 180, 255, 60))
            painter.drawRect(rect)
            painter.end()
        self.label.setPixmap(pm)

    def _save_selection(self) -> None:
        if not (self._start and self._end):
            self.accept()
            return
        rect = QRect(self._start, self._end).normalized()
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        out = self.templates_dir / f"object_{x}_{y}_{w}_{h}.png"
        grab_region(x, y, w, h, out)
        self.selected_path = out
        self.accept()