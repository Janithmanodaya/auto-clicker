from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QListWidget,
    QWidget,
    QVBoxLayout,
    QLabel,
    QToolBar,
    QFileDialog,
    QStatusBar,
)

from autoclick_pro.logging.logger import get_logger


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AutoClick Pro")
        self.resize(1200, 800)
        self.log = get_logger()

        # Toolbar
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)

        self.action_record = QAction("Record", self)
        self.action_play = QAction("Play", self)
        self.action_pause = QAction("Pause", self)
        self.action_stop = QAction("Stop", self)
        self.action_estop = QAction("E-Stop", self)
        self.action_save = QAction("Save", self)
        self.action_load = QAction("Load", self)
        self.action_export = QAction("Export", self)
        self.action_simulation = QAction("Simulation", self)
        self.action_simulation.setCheckable(True)
        self.action_simulation.setChecked(True)

        for a in (
            self.action_record,
            self.action_play,
            self.action_pause,
            self.action_stop,
            self.action_estop,
        ):
            tb.addAction(a)
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

        # Center: timeline/flow editor (placeholder list)
        self.timeline = QListWidget()
        self.timeline.addItem("Drop actions here")
        self.timeline.addItem("mouse_click")
        self.timeline.addItem("wait 500ms")
        self.timeline.addItem("key_sequence Ctrl+S")

        # Right: properties inspector
        self.props = QWidget()
        pv = QVBoxLayout(self.props)
        pv.setContentsMargins(8, 8, 8, 8)
        pv.addWidget(QLabel("Properties Inspector"))
        pv.addWidget(QLabel("Select an item to edit parameters..."))
        pv.addStretch()

        splitter.addWidget(self.tree)
        splitter.addWidget(self.timeline)
        splitter.addWidget(self.props)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 1)

        self.setCentralWidget(splitter)

        # Status bar
        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.showMessage("Ready (Simulation mode)")

        # Wire actions
        self.action_record.triggered.connect(self.on_record)
        self.action_play.triggered.connect(self.on_play)
        self.action_pause.triggered.connect(self.on_pause)
        self.action_stop.triggered.connect(self.on_stop)
        self.action_estop.triggered.connect(self.on_estop)
        self.action_save.triggered.connect(self.on_save)
        self.action_load.triggered.connect(self.on_load)
        self.action_export.triggered.connect(self.on_export)
        self.action_simulation.toggled.connect(self.on_simulation_toggled)

    # Action handlers (placeholders)
    def on_record(self):
        self.log.info("record_clicked")
        self.statusBar().showMessage("Recording...")

    def on_play(self):
        sim = self.action_simulation.isChecked()
        self.log.info("play_clicked", simulation=sim)
        self.statusBar().showMessage("Playing macro (simulation=%s)..." % sim)

    def on_pause(self):
        self.log.info("pause_clicked")
        self.statusBar().showMessage("Paused")

    def on_stop(self):
        self.log.info("stop_clicked")
        self.statusBar().showMessage("Stopped")

    def on_estop(self):
        self.log.warning("EMERGENCY_STOP_TRIGGERED")
        self.statusBar().showMessage("EMERGENCY STOP!")

    def on_save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Project", filter="Project JSON (*.json)")
        if path:
            self.log.info("save_project_clicked", path=path)
            self.statusBar().showMessage(f"Saved to {path}")

    def on_load(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Project", filter="Project JSON (*.json)")
        if path:
            self.log.info("load_project_clicked", path=path)
            self.statusBar().showMessage(f"Loaded {path}")

    def on_export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export", filter="Executable (*.exe);;All Files (*)")
        if path:
            self.log.info("export_clicked", path=path)
            self.statusBar().showMessage(f"Export target set to {path}")

    def on_simulation_toggled(self, checked: bool):
        self.log.info("simulation_mode_toggled", checked=checked)
        self.statusBar().showMessage(f"Simulation mode: {'ON' if checked else 'OFF'}")
