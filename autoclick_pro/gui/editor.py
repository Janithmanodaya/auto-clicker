from __future__ import annotations

from typing import List, Optional
import threading

from PySide6.QtCore import Qt, Signal
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
    properties inspector, and basic undo/redo.
    """
    actions_changed = Signal()
    pick_captured = Signal(int, int)  # x, y from global click picker

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
        self.input_type.addItems(["wait", "mouse_click", "key_sequence", "detect", "conditional_jump", "label", "loop_until"])
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

        # Action add row (separate buttons, no dropdown needed for adding)
        add_row = QHBoxLayout()
        self.btn_add_wait = QPushButton("Add Wait")
        self.btn_add_click_pick = QPushButton("Pick Click (X,Y)")
        self.btn_add_keyseq = QPushButton("Add Key Sequence")
        self.btn_add_label = QPushButton("Add Label")
        add_row.addWidget(self.btn_add_wait)
        add_row.addWidget(self.btn_add_click_pick)
        add_row.addWidget(self.btn_add_keyseq)
        add_row.addWidget(self.btn_add_label)

        # Buttons
        btns = QHBoxLayout()
        self.btn_add = QPushButton("Add Action")
        self.btn_remove = QPushButton("Remove Selected")
        self.btn_apply = QPushButton("Apply Changes")
        self.btn_undo = QPushButton("Undo")
        self.btn_redo = QPushButton("Redo")
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_remove)
        btns.addWidget(self.btn_apply)
        btns.addWidget(self.btn_undo)
        btns.addWidget(self.btn_redo)

        v = QVBoxLayout()
        v.addWidget(self.timeline)
        v.addLayout(add_row)
        v.addLayout(btns)

        root.addLayout(v, 2)
        root.addWidget(props, 1)

        self._undo_stack: List[List[Action]] = []
        self._redo_stack: List[List[Action]] = []

        self.btn_add.clicked.connect(self.add_action)
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_apply.clicked.connect(self.apply_changes)
        self.btn_undo.clicked.connect(self.undo)
        self.btn_redo.clicked.connect(self.redo)

        # Connect add-row actions
        self.btn_add_wait.clicked.connect(self.add_wait_action)
        self.btn_add_click_pick.clicked.connect(self.add_click_pick)
        self.btn_add_keyseq.clicked.connect(self.add_keyseq_action)
        self.btn_add_label.clicked.connect(self.add_label_action)

        self.pick_captured.connect(self._on_pick_captured)

    # Public API

    def set_actions(self, actions: List[Action]) -> None:
        self.timeline.clear()
        for a in actions:
            item = QListWidgetItem(self._format_action(a))
            item.setData(Qt.ItemDataRole.UserRole, a)
            self.timeline.addItem(item)
        self.actions_changed.emit()

    def actions(self) -> List[Action]:
        out: List[Action] = []
        for i in range(self.timeline.count()):
            item = self.timeline.item(i)
            a: Action = item.data(Qt.ItemDataRole.UserRole)
            out.append(a)
        return out

    # Undo/Redo

    def _snapshot(self) -> List[Action]:
        return [
            self.timeline.item(idx).data(Qt.ItemDataRole.UserRole)
            for idx in range(self.timeline.count())
        ]

    def _push_undo(self) -> None:
        self._undo_stack.append(self._snapshot())
        # clear redo when new change happens
        self._redo_stack.clear()

    def undo(self) -> None:
        if not self._undo_stack:
            return
        current = self._snapshot()
        prev = self._undo_stack.pop()
        self._redo_stack.append(current)
        self.set_actions(prev)

    def redo(self) -> None:
        if not self._redo_stack:
            return
        current = self._snapshot()
        nxt = self._redo_stack.pop()
        self._undo_stack.append(current)
        self.set_actions(nxt)

    # Handlers

    def add_action(self) -> None:
        # Default add remains wait for backward compatibility
        self.add_wait_action()

    def add_wait_action(self) -> None:
        self._push_undo()
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
        self.actions_changed.emit()

    def add_keyseq_action(self) -> None:
        self._push_undo()
        a = Action(
            id=f"a{self.timeline.count()+1}",
            type="key_sequence",
            target=None,
            params={"sequence": ["Hello world", "ENTER"], "text_mode": True},
        )
        item = QListWidgetItem(self._format_action(a))
        item.setData(Qt.ItemDataRole.UserRole, a)
        self.timeline.addItem(item)
        self.timeline.setCurrentItem(item)
        self.actions_changed.emit()

    def add_label_action(self) -> None:
        self._push_undo()
        name = f"label_{self.timeline.count()+1}"
        a = Action(
            id=name,
            type="label",
            target=name,
            params={},
        )
        item = QListWidgetItem(self._format_action(a))
        item.setData(Qt.ItemDataRole.UserRole, a)
        self.timeline.addItem(item)
        self.timeline.setCurrentItem(item)
        self.actions_changed.emit()

    # Click picker using a one-shot global mouse listener
    def add_click_pick(self) -> None:
        # Hide the window temporarily to avoid accidental clicks inside the app
        w = self.window()
        if w:
            w.hide()

        def _worker():
            from pynput import mouse

            def on_click(x, y, button, pressed):
                if pressed:
                    # Emit signal to UI thread and stop listener
                    self.pick_captured.emit(int(x), int(y))
                    return False
                return True

            with mouse.Listener(on_click=on_click) as listener:
                listener.join()

        threading.Thread(target=_worker, daemon=True).start()

    def remove_selected(self) -> None:
        idx = self.timeline.currentRow()
        if idx >= 0:
            self._push_undo()
            self.timeline.takeItem(idx)
            self.actions_changed.emit()

    def _on_pick_captured(self, x: int, y: int) -> None:
        # Restore window
        w = self.window()
        if w:
            w.showNormal()
            w.raise_()
            w.activateWindow()

        # Add mouse_click action with captured coordinates
        self._push_undo()
        a = Action(
            id=f"a{self.timeline.count()+1}",
            type="mouse_click",
            target=None,
            params={"x": x, "y": y, "button": "left"},
        )
        item = QListWidgetItem(self._format_action(a))
        item.setData(Qt.ItemDataRole.UserRole, a)
        self.timeline.addItem(item)
        self.timeline.setCurrentItem(item)
        self.actions_changed.emit()

    def apply_changes(self) -> None:
        item = self.timeline.currentItem()
        if not item:
            return
        self._push_undo()
        a: Action = item.data(Qt.ItemDataRole.UserRole)

        a.id = self.input_id.text().strip() or a.id
        a.type = self.input_type.currentText()
        tgt = self.input_target.text().strip()
        a.target = tgt or None

        raw = self.input_params.text().strip()
        params = {}
        if raw:
            try:
                import json
                params = json.loads(raw)
            except Exception:
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
        self.actions_changed.emit()

    def _on_selection_changed(self, cur: QListWidgetItem | None, prev: QListWidgetItem | None) -> None:
        if not cur:
            return
        a: Action = cur.data(Qt.ItemDataRole.UserRole)
        self.input_id.setText(a.id)
        idx = max(0, self.input_type.findText(a.type))
        self.input_type.setCurrentIndex(idx)
        self.input_target.setText(a.target or "")
        try:
            import json
            self.input_params.setText(json.dumps(a.params))
        except Exception:
            self.input_params.setText(str(a.params))
        self.input_delay_before.setValue(int(a.delay_before_ms))
        self.input_delay_after.setValue(int(a.delay_after_ms))
        self.input_repeat.setValue(int(a.repeat_count))

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
        elif a.type == "conditional_jump":
            params = a.params or {}
            core += f" (true->{params.get('true_target')}, false->{params.get('false_target')})"
        elif a.type == "label":
            core += f" ({a.target or a.id})"
        elif a.type == "loop_until":
            params = a.params or {}
            core += f" (label={params.get('label')}, max={params.get('max_iters', 0)})"
        return core