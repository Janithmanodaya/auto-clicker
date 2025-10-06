from __future__ import annotations

from typing import List, Dict, Tuple

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QPolygonF, QPainter
from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsTextItem,
    QGraphicsLineItem,
    QGraphicsPolygonItem,
)

from autoclick_pro.data.model import Action


class FlowView(QGraphicsView):
    """
    Visual flow view: nodes for actions, arrows with labels for sequence and branches.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.Antialiasing)

    def _arrow(self, src: QPointF, dst: QPointF, color: str = "#888", label: str | None = None):
        scene = self.scene()
        line = QGraphicsLineItem(src.x(), src.y(), dst.x(), dst.y())
        line.setPen(QPen(QColor(color), 2))
        scene.addItem(line)
        # Arrowhead
        import math
        angle = math.atan2(dst.y() - src.y(), dst.x() - src.x())
        size = 8.0
        p1 = dst
        p2 = QPointF(dst.x() - size * math.cos(angle - math.pi / 6), dst.y() - size * math.sin(angle - math.pi / 6))
        p3 = QPointF(dst.x() - size * math.cos(angle + math.pi / 6), dst.y() - size * math.sin(angle + math.pi / 6))
        tri = QGraphicsPolygonItem(QPolygonF([p1, p2, p3]))
        tri.setPen(QPen(QColor(color), 2))
        tri.setBrush(QColor(color))
        scene.addItem(tri)
        # Label
        if label:
            mid = QPointF((src.x() + dst.x()) / 2, (src.y() + dst.y()) / 2)
            t = QGraphicsTextItem(label)
            t.setPos(mid.x() + 4, mid.y() - 18)
            scene.addItem(t)

    def render_actions(self, actions: List[Action]) -> None:
        scene = self.scene()
        scene.clear()

        # Layout: improved spacing, staggered x positions by type
        x_start = 40.0
        y_start = 30.0
        dy = 90.0
        x_map = {
            "label": x_start,
            "detect": x_start + 120.0,
            "conditional_jump": x_start + 240.0,
            "loop_until": x_start + 360.0,
            "default": x_start + 180.0,
        }
        node_radius = 18.0

        id_pos: Dict[str, QPointF] = {}
        for idx, a in enumerate(actions):
            y = y_start + idx * dy
            x = x_map.get(a.type, x_map["default"])
            pos = QPointF(x, y)
            # Node circle
            circle = QGraphicsEllipseItem(pos.x() - node_radius, pos.y() - node_radius, node_radius * 2, node_radius * 2)
            circle.setPen(QPen(QColor("#4f9cf9"), 2))
            scene.addItem(circle)
            # Label
            label = QGraphicsTextItem(f"{a.id}\n{a.type}")
            label.setPos(pos.x() + node_radius + 8, pos.y() - node_radius)
            scene.addItem(label)
            id_pos[a.id] = pos

            # Sequential arrow to next
            if idx < len(actions) - 1:
                next_pos = QPointF(x_map.get(actions[idx + 1].type, x_map["default"]), y_start + (idx + 1) * dy)
                self._arrow(QPointF(pos.x(), pos.y() + node_radius), QPointF(next_pos.x(), next_pos.y() - node_radius), "#888")

        # Branches: conditional_jump true/false targets
        for a in actions:
            if a.type == "conditional_jump":
                params = a.params or {}
                src = id_pos.get(a.id)
                for key, color, text in [("true_target", "#44c767", "true"), ("false_target", "#d9534f", "false")]:
                    tgt = params.get(key)
                    if src and tgt and tgt in id_pos:
                        dst = id_pos[tgt]
                        self._arrow(QPointF(src.x() + node_radius, src.y()), QPointF(dst.x() - node_radius, dst.y()), color, text)

        # Loops: loop_until back to label
        for a in actions:
            if a.type == "loop_until":
                label_name = a.params.get("label") if a.params else None
                src = id_pos.get(a.id)
                dst = id_pos.get(label_name) or id_pos.get(label_name or "")
                if src and dst:
                    self._arrow(QPointF(src.x(), src.y() - node_radius), QPointF(dst.x(), dst.y() + node_radius), "#f0ad4e", "loop")

        rect = scene.itemsBoundingRect()
        scene.setSceneRect(QRectF(rect.x() - 40, rect.y() - 40, rect.width() + 80, rect.height() + 80))