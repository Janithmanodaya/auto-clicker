from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QWidget,
    QPushButton,
    QHBoxLayout,
)


class InstructionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("How to use AutoClick Pro")
        self.resize(820, 680)

        v = QVBoxLayout(self)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        v.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        cv = QVBoxLayout(content)
        cv.setContentsMargins(16, 16, 16, 16)
        label = QLabel()
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)

        # Simple HTML with arrows and structure
        label.setText(
            """
            <h2>Welcome to AutoClick Pro</h2>
            <p>This guide explains each major part of the app and how to use it.</p>

            <h3>Toolbar</h3>
            <ul>
              <li><b>Record</b> → Start/stop recording mouse clicks and key presses.<br/>
                  • Click <i>Record</i> to begin, click again to stop.<br/>
                  • Recorded actions are appended to the editor timeline.</li>
              <li><b>Play</b> → Run the current macro in the editor.<br/>
                  • Simulation ON by default for safety (no real inputs).<br/>
                  • Toggle <i>Simulation</i> to send real mouse/keyboard events.</li>
              <li><b>Pause</b> → Temporarily pause the macro engine.</li>
              <li><b>Stop</b> → Stop the macro engine (graceful).</li>
              <li><b>E‑Stop</b> → Emergency stop (immediate).</li>
              <li><b>Capture Object</b> → Take a screenshot and drag a selection to save a template image.<br/>
                  • The captured image can be used by <i>detect</i> actions.</li>
              <li><b>Keymap Editor</b> → Build key sequences or chords and insert them as actions.</li>
              <li><b>Label Manager</b> → Review existing labels and add a new <code>label</code> action.</li>
              <li><b>Save / Load</b> → Save or load projects as JSON.</li>
              <li><b>Export</b> → Choose a path for packaging (placeholder).</li>
              <li><b>Simulation</b> → ON/OFF toggle for sending real inputs.</li>
            </ul>

            <h3>Main Layout</h3>
            <ul>
              <li><b>Left pane</b> → Project/Macro tree.</li>
              <li><b>Center pane (Editor)</b> → Timeline of actions.<br/>
                • <b>Add Action</b> to insert a default <code>wait</code> (500 ms).<br/>
                • Select an action to edit its properties on the right.<br/>
                • Drag to reorder actions.</li>
              <li><b>Right pane</b> → Utilities and visualizers:<br/>
                • <b>Flow View</b> → Diagram of action order with arrows and branches.<br/>
                • <b>Graph Editor</b> → Nodes you can double‑click to link conditional targets.<br/>
                • <b>Saved Keymaps</b> → Store key actions and insert into the editor.</li>
            </ul>

            <h3>Common Action Types and How to Use</h3>
            <ul>
              <li><b>wait</b> → Delay for N milliseconds.<br/>
                  • Params: <code>{ "ms": 500 }</code></li>
              <li><b>mouse_click</b> → Click at (x,y) with a button.<br/>
                  • Params: <code>{ "x": 100, "y": 200, "button": "left" }</code></li>
              <li><b>key_sequence</b> → Type text or press key chords.<br/>
                  • Text mode: <code>{ "sequence": ["Hello", "ENTER"], "text_mode": true }</code><br/>
                  • Chord mode: <code>{ "sequence": ["ctrl", "s"], "text_mode": false }</code></li>
              <li><b>detect</b> → Find a template on screen.<br/>
                  • Target: path to the template image (from <i>Capture Object</i>).<br/>
                  • Params: <code>{ "conf": 0.85, "method": "template" }</code> or <code>{"method":"feature"}</code>.</li>
              <li><b>conditional_jump</b> → Branch based on a test.<br/>
                  • Params: <code>{ "test": "last_detect", "true_target": "idA", "false_target": "idB" }</code><br/>
                  • Use the <b>Graph Editor</b> and double‑click a node to link targets.</li>
              <li><b>label</b> → Marks a position to jump to.<br/>
                  • <code>target</code> (or <code>id</code>) is the label name.</li>
              <li><b>loop_until</b> → Jump back to a label until a condition is met.<br/>
                  • Params: <code>{ "label": "start", "until": {"test":"last_detect","value":true}, "max_iters": 50 }</code></li>
            </ul>

            <h3>Typical Workflow</h3>
            <ol>
              <li>Use <b>Capture Object</b> → select an area to create a template.</li>
              <li>Insert a <b>detect</b> action → set its confidence and method.</li>
              <li>Add a <b>conditional_jump</b> after detect → set true/false targets.</li>
              <li>Add a <b>label</b> named the same as your loop start.</li>
              <li>Add a <b>loop_until</b> → set <code>label</code> to the loop start and the condition.</li>
              <li>Click <b>Play</b> (Simulation ON) to verify, then turn it OFF for real inputs.</li>
            </ol>

            <h3>Troubleshooting</h3>
            <ul>
              <li>If detection fails, try a tighter template, lower conf (e.g. 0.7), or method <code>feature</code>.</li>
              <li>On Windows, if you run into permission prompts for screen capture, allow the app.</li>
              <li>Use the <b>Inspect First Detect</b> buttons to visualize matches with bounding boxes.</li>
            </ul>
            """
        )

        cv.addWidget(label)

        # Close button
        h = QHBoxLayout()
        h.addStretch()
        btn = QPushButton("Close")
        btn.clicked.connect(self.accept)
        h.addWidget(btn)
        cv.addLayout(h)