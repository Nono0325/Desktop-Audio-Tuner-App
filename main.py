"""
Desktop Audio Tuner & Equalizer Pro - Application Entry Point.
A professional native Windows desktop application for computer sound optimization and 10-band EQ tuning.
"""

import ctypes
import os
import sys
import traceback

from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox


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

    try:
        from main_window import MainWindow
        window = MainWindow()
        window.show()
        window.raise_()
        window.activateWindow()
        sys.exit(app.exec_())
    except Exception as e:
        err_msg = traceback.format_exc()
        print(f"Startup error:\n{err_msg}", file=sys.stderr)
        QMessageBox.critical(None, "啟動錯誤", f"程式啟動時發生錯誤：\n\n{str(e)}\n\n詳細資訊：\n{err_msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
