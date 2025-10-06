from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QPushButton, QHBoxLayout

from autoclick_pro.util.overlay import annotate_detection


class DetectInspector(QDialog):
    def __init__(self, parent=None, screenshot_path: Path | None = None, bbox: Tuple[int, int, int, int] | None = None, score: float = 0.0):
        super().__init__(parent)
        self.setWindowTitle("Detection Inspector")
        self.resize(800, 600)

        v = QVBoxLayout(self)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(self.image_label)

        h = QHBoxLayout()
        self.btn_close = QPushButton("Close")
        h.addStretch()
        h.addWidget(self.btn_close)
        v.addLayout(h)

        self.btn_close.clicked.connect(self.accept)

        # Render annotated image
        if screenshot_path is not None:
            annotated = annotate_detection(screenshot_path, bbox, score)
            pm = QPixmap(str(annotated))
            self.image_label.setPixmap(pm)