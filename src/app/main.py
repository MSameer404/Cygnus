# src/app/main.py
"""Cygnus — Yeolpumta Study App Clone. Entry point."""

import sys

import ctypes
import os
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QApplication

from app.data.database import init_db
from app.ui.main_window import MainWindow
from app.ui.dashboard_page import DashboardPage
from app.ui.study_page import StudyPage
from app.ui.task_page import TaskPage
from app.ui.settings_page import SettingsPage
from app.ui.syllabus_tracker_page import SyllabusTrackerPage
from app.ui.test_logs_page import TestLogsPage


def main():
    # Initialize database
    init_db()

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Cygnus")
    app.setApplicationDisplayName("Cygnus")

    # Set AppUserModelID so taskbar icon updates correctly on Windows
    if os.name == "nt":
        app_id = "cygnus.study.timer.1.0"
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except AttributeError:
            pass

    from app.core.utils import get_assets_dir
    assets_dir = get_assets_dir()

    icon_ico = assets_dir / "logo.ico"
    icon_png = assets_dir / "logo.png"

    if icon_ico.exists():
        app.setWindowIcon(QIcon(str(icon_ico)))
    elif icon_png.exists():
        app.setWindowIcon(QIcon(str(icon_png)))

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Create main window
    window = MainWindow()
    window.load_stylesheet()

    # Create pages (order must match Sidebar.PAGES)
    dashboard = DashboardPage()
    study = StudyPage()
    tasks = TaskPage()
    syllabus = SyllabusTrackerPage()
    test_logs = TestLogsPage()
    settings = SettingsPage()

    # Add pages to stack
    window.add_page(dashboard)   # 0: Dashboard
    window.add_page(study)       # 1: Study
    window.add_page(tasks)       # 2: Tasks
    window.add_page(syllabus)    # 3: Syllabus
    window.add_page(test_logs)   # 4: Test Tracker
    window.add_page(settings)    # 5: Settings

    # ---------- Keyboard shortcuts ----------
    from PyQt6.QtGui import QShortcut, QKeySequence

    # Space = play/pause timer (only when timer view is active)
    space_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), window)
    space_shortcut.activated.connect(lambda: _toggle_timer(study))

    # Escape = stop timer
    esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), window)
    esc_shortcut.activated.connect(lambda: _stop_timer(study))

    # Ctrl+1-6 = switch pages
    for i in range(6):
        shortcut = QShortcut(QKeySequence(f"Ctrl+{i + 1}"), window)
        shortcut.activated.connect(lambda idx=i: _go_page(window, idx))

    window.show()

    # Check for updates
    from app.core.updater import AutoUpdater
    updater = AutoUpdater()
    release_data = updater.check_for_updates()
    if release_data:
        updater.download_and_install(release_data, window)

    sys.exit(app.exec())


def _toggle_timer(study_page: StudyPage):
    """Toggle start/stop on the timer (if timer view is active)."""
    # Delegate to the timer page's session button handler
    study_page._timer_view._timer_page._on_session_button_clicked()


def _stop_timer(study_page: StudyPage):
    """Stop the timer immediately with Escape key."""
    from app.core.timer_engine import TimerState
    timer_engine = study_page._timer_view._timer_page.timer_engine
    if timer_engine.state == TimerState.RUNNING:
        study_page._timer_view._timer_page._stop_and_save()


def _go_page(window: MainWindow, index: int):
    window.sidebar.set_active(index)
    window.stack.setCurrentIndex(index)


if __name__ == "__main__":
    main()