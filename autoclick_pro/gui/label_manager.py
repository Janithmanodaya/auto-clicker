from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QHBoxLayout, QPushButton, QLineEdit, QLabel

from autoclick_pro.data.model import Action


class LabelManager(QDialog):
    """
    Displays labels from actions and allows adding a new label action.
    """
    def __init__(self, parent=None, actions: List[Action] | None = None):
        super().__init__(parent)
        self.setWindowTitle("Label Manager")
        self.resize(450, 400)
        v = QVBoxLayout(self)

        self.list = QListWidget()
        v.addWidget(QLabel("Existing labels"))
        v.addWidget(self.list)

        h = QHBoxLayout()
        self.input_label = QLineEdit()
        self.btn_add = QPushButton("Add Label")
        h.addWidget(self.input_label)
        h.addWidget(self.btn_add)
        v.addLayout(h)

        self.btn_close = QPushButton("Close")
        v.addWidget(self.btn_close)

        self.btn_add.clicked.connect(self.accept)
        self.btn_close.clicked.connect(self.reject)

        self._actions = actions or []
        self._populate()

    def _populate(self) -> None:
        self.list.clear()
        for a in self._actions:
            if a.type == "label":
                self.list.addItem(a.target or a.id)

    def new_label_action(self) -> Action | None:
        name = self.input_label.text().strip()
        if not name:
            return None
        return Action(id=name, type="label", target=name, params={})