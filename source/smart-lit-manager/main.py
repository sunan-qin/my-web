#!/usr/bin/env python3
"""Smart Literature Manager — AI-Assisted Academic Paper Management."""

import sys
import os
import logging

# Ensure the app root is on the path
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from app.logger import setup_logging, install_global_exception_hook
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont


def main():
    # === Bootstrap logging and error hooks ===
    log = setup_logging(logging.DEBUG)
    install_global_exception_hook()
    log.info("=== Smart Literature Manager starting ===")

    # === High-DPI support ===
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Smart Literature Manager")
    app.setOrganizationName("SmartLitManager")

    # === Optional splash screen ===
    splash = None
    try:
        splash = QSplashScreen()
        splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        splash.showMessage(
            "Smart Literature Manager  —  loading …",
            Qt.AlignBottom | Qt.AlignCenter,
            Qt.white
        )
        splash.show()
        app.processEvents()
    except Exception:
        splash = None  # Splash is best-effort

    # === Launch main window ===
    try:
        from ui.main_window import SmartLitManager
        window = SmartLitManager()
        window.show()
        if splash:
            splash.finish(window)
        log.info("Application window displayed successfully")
    except Exception as exc:
        log.critical("Failed to start main window", exc_info=True)
        QMessageBox.critical(
            None, "Startup Error",
            f"Could not start the application:\n\n{exc}\n\n"
            "Check the log file at ~/.smart-lit-manager/app.log for details."
        )
        sys.exit(1)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
