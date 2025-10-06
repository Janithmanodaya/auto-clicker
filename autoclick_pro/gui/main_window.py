from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
    QVBoxLayout,
    QLabel,
    QToolBar,
    QFileDialog,
    QStatusBar,
    QPushButton,
)

from autoclick_pro.logging.logger import get_logger
from autoclick_pro.core.engine import Engine
from autoclick_pro.gui.editor import MacroEditor
from autoclick_pro.gui.capture import CaptureDialog
from autoclick_pro.recorder.recorder import Recorder
from autoclick_pro.data.model import Action, Macro, Project
from autoclick_pro.persistence.project_io import save_project, load_project


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AutoClick Pro")
        self.resize(1200, 800)
        self.log = get_logger()

        # Engine
        self.engine = Engine()
        self.engine.on_status(lambda s: self.statusBar().showMessage(s))

        # Recorder
        self.recorder = Recorder()
        self.recording = False

        # Toolbar
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)

        style = self.style()
        self.action_record = QAction(style.standardIcon(style.SP_MediaRecord), "Record", self)
        self.action_play = QAction(style.standardIcon(style.SP_MediaPlay), "Play", self)
        self.action_pause = QAction(style.standardIcon(style.SP_MediaPause), "Pause", self)
        self.action_stop = QAction(style.standardIcon(style.SP_MediaStop), "Stop", self)
        self.action_estop = QAction(style.standardIcon(style.SP_BrowserStop), "E-Stop", self)
        self.action_save = QAction(style.standardIcon(style.SP_DialogSaveButton), "Save", self)
        self.action_load = QAction(style.standardIcon(style.SP_DialogOpenButton), "Load", self)
        self.action_export = QAction(style.standardIcon(style.SP_ComputerIcon), "Export", self)
        self.action_capture = QAction(style.standardIcon(style.SP_FileIcon), "Capture Object", self)
        self.action_simulation = QAction("Simulation", self)
        self.action_simulation.setCheckable(True)
        self.action_simulation.setChecked(True)

        # Shortcuts
        self.action_play.setShortcut("F5")
        self.action_pause.setShortcut("F6")
        self.action_stop.setShortcut("F7")
        self.action_estop.setShortcut("F8")
        self.action_record.setShortcut("F9")
        self.action_save.setShortcut("Ctrl+S")
        self.action_load.setShortcut("Ctrl+O")
        self.action_capture.setShortcut("Ctrl+Shift+C")

        for a in (
            self.action_record,
            self.action_play,
            self.action_pause,
            self.action_stop,
            self.action_estop,
        ):
            tb.addAction(a)
        tb.addSeparator()
        tb.addAction(self.action_capture)
        tb.addSeparator()
        for a in (self.action_save, self.action_load, self.action_export):
            tb.addAction(a)
        tb.addSeparator()
        tb.addAction(self.action_simulation)

        # Three-pane layout
        splitter = QSplitter(Qt.Horizontal, self)

        # Left: projects/macros tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Projects / Macros"])
        demo = QTreeWidgetItem(["Sample Project"])
        demo_macro = QTreeWidgetItem(["Hello Macro"])
        demo.addChild(demo_macro)
        self.tree.addTopLevelItem(demo)
        self.tree.expandAll()

        # Center: macro editor
        self.editor = MacroEditor()
        # Seed with a simple demo
        self.editor.set_actions(
            [
                Action(id="a1", type="mouse_click", params={"x": None, "y": None, "button": "left"}),
                Action(id="a2", type="wait", params={"ms": 500}),
                Action(id="a3", type="key_sequence", params={"sequence": ["Hello from AutoClick Pro!", "ENTER"]}),
            ]
        )

        # Right: properties / utilities
        self.props = QWidget()
        pv = QVBoxLayout(self.props)
        pv.setContentsMargins(8, 8, 8, 8)
        pv.addWidget(QLabel("Utilities"))
        self.btn_detect_demo = QPushButton("Run Detect on First 'detect' Action")
        pv.addWidget(self.btn_detect_demo)
        pv.addStretch()

        splitter.addWidget(self.tree)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.props)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)

        self.setCentralWidget(splitter)

        # Status bar
        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.showMessage("Ready")
        self.sim_label = QLabel("Simulation: ON")
        sb.addPermanentWidget(self.sim_la_codebenewl</)
)

        # Wire actions
        self.action_record.triggered.connect(self.on_record)
        self.action_play.triggered.connect(self.on_play)
        self.action_pause.triggered.connect(lambda: self.engine.pause())
        self.action_stop.triggered.connect(lambda: self.engine.stop())
        self.action_estop.triggered.connect(lambda: self.engine.estop())
        self.action_save.triggered.connect(self.on_save)
        self.action_load.triggered.connect(self.on_load)
        self.action_export.triggered.connect(self.on_export)
        self.action_simulation.toggled.connect(self.on_simulation_toggled)
        self.action_capture.triggered.connect(self.on_capture)
        self.btn_detect_demo.clicked.connect(self.on_detect_demo)

    # Action handlers
    def on_record(self):
        if not self.recording:
            self.recorder.start()
            self.recording = True
            self.log.info("record_started")
            self.statusBar().showMessage("Recording... (click Record again to stop)")
            self.action_record.setText("Stop Recording")
        else:
            actions = self.recorder.stop()
            self.recording = False
            self.action_record.setText("Record")
            self.log.info("record_finished", count=len(actions))
            self.statusBar().showMessage(f"Recorded {len(actions)} actions")
            # Append recorded actions to editor
            existing = self.editor.actions()
            self.editor.set_actions(existing + actions)

    def on_play(self):
        sim = self.action_simulation.isChecked()
        self.log.info("play_clicked", simulation=sim)
        self.engine.set_simulation(sim)
        self.statusBar().showMessage("Playing macro (simulation=%s)..." % sim)

        # Build action dicts from editor
        acts = []
        for a in self.editor.actions():
            acts.append(
                {
                    "id": a.id,
                    "type": a.type,
                    "target": a.target,
                    "params": a.params,
                    "delay_before_ms": a.delay_before_ms,
                    "delay_after_ms": a.delay_after_ms,
                    "repeat_count": a.repeat_count,
                }
            )
        self.engine.start(acts)

    def on_save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Project", filter="Project JSON (*.json)")
        if not path:
            return
        proj = Project(
            name="Project",
            macros=[Macro(id="m1", name="Macro 1", timeline=self.editor.actions())],
            objects=[],
        )
        save_project(Path(path), proj)
        self.log.info("project_saved", path=path)
        self.statusBar().showMessage(f"Saved to {path}")

    def on_load(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Project", filter="Project JSON (*.json)")
        if not path:
            return
        proj = load_project(Path(path))
        actions = proj.macros[0].timeline if proj.macros else []
        self.editor.set_actions(actions)
        self.log.info("project_loaded", path=path, actions=len(actions))
        self.statusBar().showMessage(f"Loaded {path}")

    def on_export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export", filter="Executable (*.exe);;All Files (*)")
        if path:
            self.log.info("export_clicked", path=path)
            self.statusBar().showMessage(f"Export target set to {path}")

    def on_simulation_toggled(self, checked: bool):
        self.log.info("simulation_mode_toggled", checked=checked)
        self.sim_label.setText(f"Simulation: {'ON' if checked else 'OFF'}")
        self.statusBar().showMessage(f"Simulation mode: {'ON' if checked else 'OFF'}")

    def on_capture(self):
        dlg = CaptureDialog(self, templates_dir=Path("templates"))
        if dlg.exec():
            tmpl_path = getattr(dlg, "selected_path", None)
            if tmpl_path:
                # Add a detect action pointing to captured template
                actions = self.editor.actions()
                actions.append(Action(id=f"a{len(actions)+1}", type="detect", target=str(tmpl_path), params={"conf": 0.85}))
                self.editor.set_actions(actions)
                self.log.info("capture_added_detect", path=str(tmpl_path))
                self.statusBar().showMessage(f"Captured template: {tmpl_path}")

    def on_detect_demo(self):
        # Execute first detect action via engine (simulation mode does not affect detect)
        for a in self.editor.actions():
            if a.type == "detect":
                self.engine._execute({"id": a.id, "type": "detect", "target": a.target, "params": a.params})
                break
