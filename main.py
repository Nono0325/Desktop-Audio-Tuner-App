"""
Desktop Audio Tuner & Equalizer Pro - Application Entry Point.
A professional native Windows desktop application for computer sound optimization and 10-band EQ tuning.
"""

import ctypes
import os
import sys

from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from main_window import MainWindow


def main():
    # Set Windows App User Model ID so custom icon shows properly in Windows Taskbar
    try:
        app_id = "nono.desktop_audio_tuner.pro.v1"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass

    # High DPI Scaling for 2K/4K displays
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Desktop Audio Tuner Pro")
    app.setOrganizationName("Nono")

    # Set Application Icon
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "app_icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
