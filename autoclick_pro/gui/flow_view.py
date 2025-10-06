from __future__ import annotations

from typing import List, Dict

from PySide6.QtCore import QPointF
from PySide6.QtGui import QPen, QColor
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsLineItem

from autoclick_pro.data.model import Action


class FlowView(QGraphicsView):
    """
    Minimal visual flow view: nodes for actions, arrows for sequence and branches.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(self.RenderHint.Antialiasing)

    def render_actions(self, actions: List[Action]) -> None:
        scene = self.scene()
        scene.clear()

        # Layout: vertical list with spacing
        x0, y0 = 20.0, 20.0
        dy = 70.0
        node_radius = 18.0

        id_pos: Dict[str, QPointF] = {}
        for idx, a in enumerate(actions):
            y = y0 + idx * dy
            pos = QPointF(x0, y)
            # Node circle
            circle = QGraphicsEllipseItem(pos.x() - node_radius, pos.y() - node_radius, node_radius * 2, node_radius * 2)
            circle.setPen(QPen(QColor("#4f9cf9"), 2))
            scene.addItem(circle)
            # Label
            label = QGraphicsTextItem(f"{a.id}\n{a.type}")
            label.setPos(pos.x() + node_radius + 6, pos.y() - node_radius)
            scene.addItem(label)
            id_pos[a.id] = pos

            # Sequential arrow to next
            if idx < len(actions) - 1:
                next_pos = QPointF(x0, y0 + (idx + 1) * dy)
                line = QGraphicsLineItem(pos.x(), pos.y() + node_radius, next_pos.x(), next_pos.y() - node_radius)
                line.setPen(QPen(QColor("#888"), 1))
                scene.addItem(line)

        # Branches: conditional_jump true/false targets
        for a in actions:
            if a.type == "conditional_jump":
                params = a.params or {}
                for key, color in [("true_target", "#44c767"), ("false_target", "#d9534f")]:
                    tgt = params.get(key)
                    if tgt and tgt in id_pos:
                        src = id_pos.get(a.id)
                        dst = id_pos[tgt]
                        if src:
                            line = QGraphicsLineItem(src.x() + node_radius, src.y(), dst.x() - node_radius, dst.y())
                            line.setPen(QPen(QColor(color), 2))
                            scene.addItem(line)

        # Loops: loop_until back to label
        for a in actions:
            if a.type == "loop_until":
                label_name = a.params.get("label") if a.params else None
                src = id_pos.get(a.id)
                dst = id_pos.get(label_name) or id_pos.get(label_name or "")
                if src and dst:
                    line = QGraphicsLineItem(src.x(), src.y() - node_radius, dst.x(), dst.y() + node_radius)
                    line.setPen(QPen(QColor("#f0ad4e"), 2))
                    scene.addItem(line)

        self.setSceneRect(scene.itemsBoundingRect().adjusted(0, 0, 60, 60))