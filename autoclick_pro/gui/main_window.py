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
    QStyle,
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
        # Show text beside icons to improve readability on dark backgrounds
        tb.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(tb)

        style = self.style()

        # Helper to resolve a standard icon with fallbacks across Qt/PySide versions
        def std_icon(*candidates: str):
            for name in candidates:
                sp = getattr(QStyle, name, None)
                if sp is not None:
                    return style.standardIcon(sp)
            # last-resort generic icon
            return style.standardIcon(QStyle.SP_MessageBoxInformation)

        # Qt does not provide a MediaRecord standard icon; use Apply/Yes/Ok as reasonable substitutes
        self.action_record = QAction(std_icon("SP_DialogApplyButton", "SP_DialogYesButton", "SP_DialogOkButton"), "Record", self)
        self.action_play = QAction(std_icon("SP_MediaPlay", "SP_ArrowForward"), "Play", self)
        self.action_pause = QAction(std_icon("SP_MediaPause", "SP_MediaStop"), "Pause", self)
        self.action_stop = QAction(std_icon("SP_MediaStop", "SP_BrowserStop"), "Stop", self)
        self.action_estop = QAction(std_icon("SP_BrowserStop", "SP_MessageBoxCritical"), "E-Stop", self)
        self.action_save = QAction(std_icon("SP_DialogSaveButton", "SP_DialogApplyButton"), "Save", self)
        self.action_load = QAction(std_icon("SP_DialogOpenButton", "SP_DirOpenIcon" if hasattr(QStyle, "SP_DirOpenIcon") else "SP_DialogOpenButton"), "Load", self)
        self.action_export = QAction(std_icon("SP_ComputerIcon", "SP_DriveHDIcon"), "Export", self)
        self.action_capture = QAction(std_icon("SP_FileIcon", "SP_DialogOpenButton"), "Capture Object", self)
        self.action_simulation = QAction("Simulation", self)
        self.action_simulation.setCheckable(True)
        # Default to real execution; enable this to simulate without performing real clicks/keys
        self.action_simulation.setChecked(False)

        # Shortcuts
        self.action_play.setShortcut("F5")
        self.action_pause.setShortcut("F6")
        self.action_stop.setShortcut("F7")
        self.action_estop.setShortcut("F8")
        self.action_record.setShortcut("F9")
        self.action_save.setShortcut("Ctrl+S")
        self.action_load.setShortcut("Ctrl+O")
        self.action_capture.setShortcut("Ctrl+Shift+C")

        # Keymap editor action
        self.action_keymap = QAction(std_icon("SP_DirIcon", "SP_DirOpenIcon", "SP_DialogOpenButton"), "Keymap Editor", self)
        # Label manager action
        self.action_label_manager = QAction(std_icon("SP_DialogYesButton", "SP_DialogOkButton", "SP_DialogApplyButton"), "Label Manager", self)

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
        tb.addAction(self.action_keymap)
        tb.addAction(self.action_label_manager)
        tb.addSeparator()
        for a in (self.action_save, self.action_load, self.action_export):
            tb.addAction(a)
        tb.addSeparator()
        # Instructions/help
        self.action_instructions = QAction(std_icon("SP_MessageBoxInformation", "SP_DialogHelpButton"), "Instructions", self)
        tb.addAction(self.action_instructions)
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

        # Detection test buttons
        self.btn_detect_demo = QPushButton("Inspect First Detect (Template)")
        pv.addWidget(self.btn_detect_demo)
        self.btn_detect_feature = QPushButton("Inspect First Detect (Feature)")
        pv.addWidget(self.btn_detect_feature)

        # Loop/label test
        self.btn_loop_test = QPushButton("Test Loop Until Detect")
        pv.addWidget(self.btn_loop_test)

        # Keymap list manager
        pv.addWidget(QLabel("Saved Keymaps"))
        from PySide6.QtWidgets import QListWidget
        self.keymap_list = QListWidget()
        pv.addWidget(self.keymap_list)
        self.btn_add_keymap = QPushButton("Add From Keymap Editor")
        pv.addWidget(self.btn_add_keymap)
        self.btn_insert_keymap = QPushButton("Insert Selected Keymap")
        pv.addWidget(self.btn_insert_keymap)

        pv.addStretch()

        splitter.addWidget(self.tree)
        splitter.addWidget(self.editor)

        # Flow view
        from autoclick_pro.gui.flow_view import FlowView
        self.flow = FlowView()
        self.editor.actions_changed.connect(lambda: self.flow.render_actions(self.editor.actions()))
        self.flow.render_actions(self.editor.actions())

        # Put flow view under utilities
        pv.addWidget(QLabel("Flow View"))
        pv.addWidget(self.flow)

        # Graph-based timeline editor
        from autoclick_pro.gui.graph_editor import GraphEditor
        pv.addWidget(QLabel("Graph Editor (Double-click a node to link targets)"))
        self.graph = GraphEditor()
        pv.addWidget(self.graph)
        self.graph.render_actions(self.editor.actions())
        self.editor.actions_changed.connect(lambda: (self.flow.render_actions(self.editor.actions()), self.graph.render_actions(self.editor.actions())))

        # Link mode for conditional jumps
        from PySide6.QtWidgets import QHBoxLayout, QRadioButton
        link_row = QHBoxLayout()
        pv.addLayout(link_row)
        self.rb_true = QRadioButton("Link TRUE")
        self.rb_false = QRadioButton("Link FALSE")
        self.rb_true.setChecked(True)
        link_row.addWidget(self.rb_true)
        link_row.addWidget(self.rb_false)

        self.graph.node_activated.connect(self.on_graph_node_activated)

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
        sb.addPermanentWidget(self.sim_label)

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
        self.action_keymap.triggered.connect(self.on_keymap)
        self.action_label_manager.triggered.connect(self.on_label_manager)
        self.action_instructions.triggered.connect(self.on_instructions)
        self.btn_detect_demo.clicked.connect(self.on_detect_demo)
        self.btn_detect_feature.clicked.connect(self.on_detect_feature)
        self.btn_loop_test.clicked.connect(self.on_loop_test)
        self.btn_add_keymap.clicked.connect(self.on_keymap_add_to_list)
        self.btn_insert_keymap.clicked.connect(self.on_keymap_insert_selected)

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

    def on_keymap(self):
        from autoclick_pro.gui.keymap_editor import KeymapEditor
        dlg = KeymapEditor(self)
        if dlg.exec():
            act = dlg.result_action()
            if act:
                # Append as Action object
                from autoclick_pro.data.model import Action as ActionModel
                a = ActionModel(id=f"a{len(self.editor.actions())+1}", type=act["type"], target=None, params=act.get("params", {}))
                actions = self.editor.actions()
                actions.append(a)
                self.editor.set_actions(actions)
                self.flow.render_actions(actions)
                self.graph.render_actions(actions)
                self.log.info("keymap_added_action", params=act.get("params"))
                self.statusBar().showMessage("Keymap action added")

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
        # Visual inspector for first detect action (template)
        from autoclick_pro.util.screen import grab_screen
        from autoclick_pro.detect.template_matcher import match_template
        from autoclick_pro.gui.detect_inspector import DetectInspector

        for a in self.editor.actions():
            if a.type == "detect":
                screen = grab_screen()
                conf = float(a.params.get("conf", 0.85))
                res = match_template(Path(screen), Path(str(a.target)), confidence_threshold=conf)
                dlg = DetectInspector(self, screenshot_path=Path(screen), bbox=res.bbox, score=res.score)
                dlg.exec()
                break

    def on_detect_feature(self):
        # Visual inspector for first detect action using feature matching
        from autoclick_pro.util.screen import grab_screen
        from autoclick_pro.detect.feature_matcher import feature_match
        from autoclick_pro.gui.detect_inspector import DetectInspector

        for a in self.editor.actions():
            if a.type == "detect":
                screen = grab_screen()
                conf = float(a.params.get("conf", 0.5))
                res = feature_match(Path(screen), Path(str(a.target)), confidence_threshold=conf)
                cands = [ (c.bbox, c.score) for c in res.candidates ]
                first = cands[0] if cands else ((None), 0.0)
                bbox = first[0] if cands else None
                score = first[1] if cands else 0.0
                dlg = DetectInspector(self, screenshot_path=Path(screen), bbox=bbox, score=score, candidates=cands)
                dlg.exec()
                break

    def on_label_manager(self):
        from autoclick_pro.gui.label_manager import LabelManager
        dlg = LabelManager(self, actions=self.editor.actions())
        if dlg.exec():
            new_label = dlg.new_label_action()
            if new_label:
                actions = self.editor.actions()
                actions.append(new_label)
                self.editor.set_actions(actions)
                self.flow.render_actions(actions)
                self.graph.render_actions(actions)
                self.statusBar().showMessage(f"Label '{new_label.target}' added")

    def on_graph_node_activated(self, target_id: str):
        # Link selected node to current conditional jump
        item = self.editor.timeline.currentItem()
        if not item:
            self.statusBar().showMessage("Select a conditional_jump action in the editor first.")
            return
        a = item.data(Qt.ItemDataRole.UserRole)
        if not a or a.type != "conditional_jump":
            self.statusBar().showMessage("Current selection is not a conditional_jump.")
            return
        params = dict(a.params or {})
        if self.rb_true.isChecked():
            params["true_target"] = target_id
        else:
            params["false_target"] = target_id
        a.params = params
        item.setData(Qt.ItemDataRole.UserRole, a)
        item.setText(self.editor._format_action(a))
        self.flow.render_actions(self.editor.actions())
        self.graph.render_actions(self.editor.actions())
        self.statusBar().showMessage(f"Linked conditional to {target_id} ({'true' if self.rb_true.isChecked() else 'false'})")

    def on_loop_test(self):
        # Build a demo macro: label -> detect -> conditional_jump -> loop_until
        actions = [
            {"id": "lbl1", "type": "label", "target": "start"},
            {"id": "d1", "type": "detect", "target": self._first_detect_target(), "params": {"conf": 0.85, "method": "template"}},
            {"id": "cj1", "type": "conditional_jump", "params": {"test": "last_detect", "true_target": "done", "false_target": "loop"}},
            {"id": "loop", "type": "loop_until", "params": {"label": "start", "until": {"test": "last_detect", "value": True}, "max_iters": 50}},
            {"id": "done", "type": "key_sequence", "params": {"sequence": ["Detection succeeded", "ENTER"], "text_mode": True}},
        ]
        self.engine.set_simulation(True)  # keep simulation for safety
        self.engine.start(actions)

    def _first_detect_target(self) -> str | None:
        for a in self.editor.actions():
            if a.type == "detect" and a.target:
                return str(a.target)
        return None

    def on_keymap_add_to_list(self):
        # Use keymap editor to create and store an action in the list
        from autoclick_pro.gui.keymap_editor import KeymapEditor
        dlg = KeymapEditor(self)
        if dlg.exec():
            act = dlg.result_action()
            if act:
                from PySide6.QtWidgets import QListWidgetItem
                item = QListWidgetItem(str(act.get("params")))
                item.setData(Qt.ItemDataRole.UserRole, act)
                self.keymap_list.addItem(item)

    def on_keymap_insert_selected(self):
        # Insert selected keymap action into macro editor
        item = self.keymap_list.currentItem()
        if not item:
            return
        act = item.data(Qt.ItemDataRole.UserRole)
        from autoclick_pro.data.model import Action as ActionModel
        a = ActionModel(id=f"a{len(self.editor.actions())+1}", type=act["type"], target=None, params=act.get("params", {}))
        actions = self.editor.actions()
        actions.append(a)
        self.editor.set_actions(actions)
        self.flow.render_actions(actions)
        self.graph.render_actions(actions)
        self.statusBar().showMessage("Inserted keymap action into macro")

    def on_instructions(self):
        # Open instructions/help dialog
        from autoclick_pro.gui.instructions import InstructionsDialog
        dlg = InstructionsDialog(self)
        dlg.exec()
