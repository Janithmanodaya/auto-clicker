import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer

from autoclick_pro.gui.main_window import MainWindow
from autoclick_pro.logging.logger import configure_logging
from autoclick_pro.gui.styles import DARK_QSS


def main():
    configure_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("AutoClick Pro")
    app.setOrganizationName("AutoClick Pro")
    app.setOrganizationDomain("autoclickpro.local")

    # High DPI and font rendering hints
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Apply theme
    app.setStyleSheet(DARK_QSS)

    window = MainWindow()
    window.show()

    # Keep UI responsive even under heavy worker load
    # by pumping events periodically
    timer = QTimer()
    timer.setInterval(50)
    timer.timeout.connect(lambda: None)
    timer.start()

    sys.exit(app.exec())