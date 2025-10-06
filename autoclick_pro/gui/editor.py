from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
    QPushButton,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QLabel,
)

from autoclick_pro.data.model import Action


class MacroEditor(QWidget):
    """
    Simple list-based macro editor with reorder, add/remove actions,
    and a properties inspector for the selected action.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        root = QHBoxLayout(self)

        # Timeline list
        self.timeline = QListWidget()
        self.timeline.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.timeline.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.timeline.setAlternatingRowColors(True)
        self.timeline.setUniformItemSizes(True)
        self.timeline.currentItemChanged.connect(self._on_selection_changed)

        # Right properties panel
        props = QWidget()
        pf = QFormLayout(props)
        pf.setContentsMargins(8, 8, 8, 8)

        self.input_id = QLineEdit()
        self.input_type = QComboBox()
        self.input_type.addItems(["wait", "mouse_click", "key_sequence", "detect"])
        self.input_target = QLineEdit()
        self.input_params = QLineEdit()
        self.input_delay_before = QSpinBox()
        self.input_delay_before.setRange(0, 60_000)
        self.input_delay_after = QSpinBox()
        self.input_delay_after.setRange(0, 60_000)
        self.input_repeat = QSpinBox()
        self.input_repeat.setRange(1, 10_000)

        pf.addRow(QLabel("ID"), self.input_id)
        pf.addRow(QLabel("Type"), self.input_type)
        pf.addRow(QLabel("Target"), self.input_target)
        pf.addRow(QLabel("Params (JSON)"), self.input_params)
        pf.addRow(QLabel("Delay before (ms)"), self.input_delay_before)
        pf.addRow(QLabel("Delay after (ms)"), self.input_delay_after)
        pf.addRow(QLabel("Repeat count"), self.input_repeat)

        # Buttons
        btns = QHBoxLayout()
        self.btn_add = QPushButton("Add Action")
        self.btn_remove = QPushButton("Remove Selected")
        self.btn_apply = QPushButton("Apply Changes")
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_remove)
        btns.addWidget(self.btn_apply)

        v = QVBoxLayout()
        v.addWidget(self.timeline)
        v.addLayout(btns)

        root.addLayout(v, 2)
        root.addWidget(props, 1)

        self.btn_add.clicked.connect(self.add_action)
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_apply.clicked.connect(self.apply_changes)

    # Public API

    def set_actions(self, actions: List[Action]) -> None:
        self.timeline.clear()
        for a in actions:
            item = QListWidgetItem(self._format_action(a))
            item.setData(Qt.ItemDataRole.UserRole, a)
            self.timeline.addItem(item)

    def actions(self) -> List[Action]:
        out: List[Action] = []
        for i in range(self.timeline.count()):
            item = self.timeline.item(i)
            a: Action = item.data(Qt.ItemDataRole.UserRole)
            out.append(a)
        return out

    # Handlers

    def add_action(self) -> None:
        a = Action(
            id=f"a{self.timeline.count()+1}",
            type="wait",
            target=None,
            params={"ms": 500},
            delay_before_ms=0,
            delay_after_ms=0,
            repeat_count=1,
        )
        item = QListWidgetItem(self._format_action(a))
        item.setData(Qt.ItemDataRole.UserRole, a)
        self.timeline.addItem(item)
        self.timeline.setCurrentItem(item)

    def remove_selected(self) -> None:
        idx = self.timeline.currentRow()
        if idx >= 0:
            self.timeline.takeItem(idx)

    def apply_changes(self) -> None:
        item = self.timeline.currentItem()
        if not item:
            return
        a: Action = item.data(Qt.ItemDataRole.UserRole)

        # Update from inspector
        a.id = self.input_id.text().strip() or a.id
        a.type = self.input_type.currentText()
        tgt = self.input_target.text().strip()
        a.target = tgt or None

        # Params as JSON-like simple parser: key=value pairs separated by commas
        raw = self.input_params.text().strip()
        params = {}
        if raw:
            try:
                import json
                params = json.loads(raw)
            except Exception:
                # Fallback: key=value, comma-separated
                for part in raw.split(","):
                    if "=" in part:
                        k, v = part.split("=", 1)
                        params[k.strip()] = v.strip()
        a.params = params

        a.delay_before_ms = int(self.input_delay_before.value())
        a.delay_after_ms = int(self.input_delay_after.value())
        a.repeat_count = int(self.input_repeat.value())

        item.setText(self._format_action(a))
        item.setData(Qt.ItemDataRole.UserRole, a)

    def _on_selection_changed(self, cur: QListWidgetItem | None, prev: QListWidgetItem | None) -> None:
        if not cur:
            return
        a: Action = cur.data(Qt.ItemDataRole.UserRole)
        self.input_id.setText(a.id)
        idx = max(0, self.input_type.findText(a.type))
        self.input_type.setCurrentIndex(idx)
        self.input_target.setText(a.target or "")
        # Show params as JSON
        try:
            import json
            self.input_params.setText(json.dumps(a.params))
        except Exception:
            self.input_params.setText(str(a.params))
        self.input_delay_before.setValue(int(a.delay_before_ms))
        self.input_delay_after.setValue(int(a.delay_after_ms))
        self.input_repeat.setValue(int(a.repeat_count))

    # Utils

    def _format_action(self, a: Action) -> str:
        core = f"{a.id}: {a.type}"
        if a.type == "wait":
            ms = a.params.get("ms", 0)
            core += f" ({ms} ms)"
        elif a.type == "mouse_click":
            x = a.params.get("x")
            y = a.params.get("y")
            btn = a.params.get("button", "left")
            core += f" ({btn} @ {x},{y})"
        elif a.type == "key_sequence":
            seq = a.params.get("sequence", [])
            core += f" ({' '.join(map(str, seq))})"
        elif a.type == "detect":
            tgt = a.target or ""
            thr = a.params.get("conf", "")
            core += f" ({tgt}, conf={thr})"
        return core