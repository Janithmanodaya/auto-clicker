DARK_QSS = """
QWidget {
    background-color: #1e1f22;
    color: #e0e0e0;
    font-size: 12px;
}

QMainWindow::separator {
    background: #2a2c30;
}

QToolBar {
    background: #24262a;
    border-bottom: 1px solid #34363b;
    spacing: 6px;
}

QToolButton {
    background: transparent;
    padding: 6px 10px;
    border-radius: 6px;
}
QToolButton:hover {
    background: #2f3238;
}
QToolButton:pressed {
    background: #3a3d45;
}

QSplitter::handle {
    background: #2a2c30;
}

QTreeWidget, QListWidget {
    background: #232428;
    border: 1px solid #34363b;
    padding: 4px;
}
QTreeWidget::item:selected, QListWidget::item:selected {
    background: #334155;
    color: #e0e0e0;
}
QListWidget::item {
    padding: 6px;
}

QLabel {
    color: #e0e0e0;
}

QLineEdit, QSpinBox, QComboBox {
    background: #2a2c30;
    color: #e0e0e0;
    border: 1px solid #3a3d45;
    border-radius: 4px;
    padding: 4px 6px;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #4f9cf9;
}

QPushButton {
    background: #2f80ed;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 6px;
}
QPushButton:hover {
    background: #3b89f0;
}
QPushButton:disabled {
    background: #3a3d45;
    color: #b0b0b0;
}

QStatusBar {
    background: #24262a;
    border-top: 1px solid #34363b;
}
"""