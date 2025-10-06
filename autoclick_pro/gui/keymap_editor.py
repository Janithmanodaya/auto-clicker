from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QCheckBox,
    QLineEdit,
    QLabel,
)

KEYS = [
    ["ESC", "F1", "F2", "F3", "F4"],
    ["`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "BACKSPACE"],
    ["TAB", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", "\\"],
    ["CAPSLOCK", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "ENTER"],
    ["SHIFT", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "SHIFT"],
    ["CTRL", "ALT", "META", "SPACE", "ALT", "CTRL"],
]


class KeymapEditor(QDialog):
    """
    Simple keymap editor for chords and sequences.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keymap Editor")
        self.resize(700, 400)

        v = QVBoxLayout(self)

        # Mode selection
        hmode = QHBoxLayout()
        self.chk_chord = QCheckBox("Chord")
        self.chk_sequence = QCheckBox("Sequence")
        self.chk_chord.setChecked(True)
        self.chk_sequence.setChecked(False)
        self.chk_chord.toggled.connect(lambda c: self.chk_sequence.setChecked(not c))
        self.chk_sequence.toggled.connect(lambda c: self.chk_chord.setChecked(not c))
        hmode.addWidget(self.chk_chord)
        hmode.addWidget(self.chk_sequence)
        hmode.addStretch()
        v.addLayout(hmode)

        # Modifiers
        hmods = QHBoxLayout()
        self.mod_ctrl = QCheckBox("Ctrl")
        self.mod_shift = QCheckBox("Shift")
        self.mod_alt = QCheckBox("Alt")
        self.mod_meta = QCheckBox("Meta")
        hmods.addWidget(self.mod_ctrl)
        hmods.addWidget(self.mod_shift)
        hmods.addWidget(self.mod_alt)
        hmods.addWidget(self.mod_meta)
        hmods.addStretch()
        v.addLayout(hmods)

        # Keyboard grid
        grid = QGridLayout()
        self.selected_keys: List[str] = []
        self.key_buttons: dict[str, QPushButton] = {}
        row = 0
        for row_keys in KEYS:
            col = 0
            for k in row_keys:
                btn = QPushButton(k)
                btn.setCheckable(True)
                btn.clicked.connect(lambda _, name=k: self._toggle_key(name))
                grid.addWidget(btn, row, col)
                self.key_buttons[k] = btn
                col += 1
            row += 1
        v.addLayout(grid)

        # Sequence line edit
        hseq = QHBoxLayout()
        hseq.addWidget(QLabel("Sequence text:"))
        self.input_sequence = QLineEdit()
        hseq.addWidget(self.input_sequence)
        v.addLayout(hseq)

        # Save/cancel
        h = QHBoxLayout()
        self.btn_save = QPushButton("Save")
        self.btn_cancel = QPushButton("Cancel")
        h.addStretch()
        h.addWidget(self.btn_save)
        h.addWidget(self.btn_cancel)
        v.addLayout(h)

        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def _toggle_key(self, name: str) -> None:
        if name in self.selected_keys:
            self.selected_keys.remove(name)
        else:
            self.selected_keys.append(name)
        # Visual toggle
        btn = self.key_buttons.get(name)
        if btn:
            btn.setChecked(name in self.selected_keys)

    def result_action(self) -> dict | None:
        """
        Returns a key_sequence or chord action dict for the macro editor.
        """
        if self.chk_chord.isChecked():
            keys: List[str] = []
            if self.mod_ctrl.isChecked():
                keys.append("ctrl")
            if self.mod_shift.isChecked():
                keys.append("shift")
            if self.mod_alt.isChecked():
                keys.append("alt")
            if self.mod_meta.isChecked():
                keys.append("cmd")
            keys.extend([k.lower() for k in self.selected_keys if k not in {"CTRL", "SHIFT", "ALT", "META"}])
            if not keys:
                return None
            return {"type": "key_sequence", "params": {"sequence": keys, "text_mode": False}}
        else:
            txt = self.input_sequence.text().strip()
            if not txt:
                return None
            # Split by whitespace, treat ENTER/TAB/ESC specially
            seq = [part for part in txt.split()]
            return {"type": "key_sequence", "params": {"sequence": seq, "text_mode": True}}