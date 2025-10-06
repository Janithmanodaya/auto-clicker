from __future__ import annotations

from typing import List, Dict

from PySide6.QtCore import QPointF, Signal
from PySide6.QtGui import QPen, QColor
from PySide6.QtWidgets import (
    QWidget,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsTextItem,
    QVBoxLayout,
)

from autoclick_pro.data.model import Action


class GraphEditor(QWidget):
    """
    Minimal graph-based editor:
    - Displays actions as nodes in a scene (draggable by default via the view's item flags).
    - Double-click a node to emit node_activated(action_id) for linking.
    """
    node_activated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        self.view = QGraphicsView()
        self.scene = QGraphicsScene(self.view)
        self.view.setScene(self.scene)
        self.view.setRenderHint(self.view.RenderHint.Antialiasing)
        v.addWidget(self.view)

        # Node registry
        self._nodes: Dict[str, QGraphicsEllipseItem] = {}

    def render_actions(self, actions: List[Action]) -> None:
        self.scene.clear()
        self._nodes.clear()

        # Simple grid layout
        x0, y0 = 30.0, 30.0
        dx, dy = 200.0, 120.0
        per_row = 3
        radius = 20.0

        for idx, a in enumerate(actions):
            row = idx // per_row
            col = idx % per_row
            x = x0 + col * dx
            y = y0 + row * dy
            circle = QGraphicsEllipseItem(x, y, radius * 2, radius * 2)
            circle.setPen(QPen(QColor("#4f9cf9"), 2))
            circle.setData(0, a.id)  # store id
            circle.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, True)
            circle.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)
            self.scene.addItem(circle)
            self._nodes[a.id] = circle

            label = QGraphicsTextItem(f"{a.id}\n{a.type}")
            label.setPos(x + radius * 2 + 6, y - 2)
            self.scene.addItem(label)

        # Connect double-click via scene event filter-like approach
        self.scene.mouseDoubleClickEvent = self._on_double_click  # type: ignore

    def _on_double_click(self, event):
        pos = event.scenePos()
        items = self.scene.items(pos)
        for it in items:
            if isinstance(it, QGraphicsEllipseItem):
                action_id = it.data(0)
                if action_id:
                    self.node_activated.emit(str(action_id))
                    break
        # Call base handler
        super(QGraphicsScene, self.scene).mouseDoubleClickEvent(event)