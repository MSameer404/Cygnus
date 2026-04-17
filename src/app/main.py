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
from app.ui.timer_page import TimerPage
from app.ui.stats_page import StatsPage
from app.ui.task_page import TaskPage
from app.ui.settings_page import SettingsPage


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

    # Load and set application icon (prioritize .ico for Windows)
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        # PyInstaller puts `main.py` at root `_MEIPASS`, but `assets` are at `app/assets`
        assets_dir = Path(sys._MEIPASS) / "app" / "assets"
    else:
        # Running normally
        assets_dir = Path(__file__).parent / "assets"

    icon_ico = assets_dir / "logo.ico"
    icon_png = assets_dir / "logo.png"

    if icon_ico.exists():
        app.setWindowIcon(QIcon(str(icon_ico)))
        # Make sure main window also picks up this icon explicitly for some Windows systems
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
    timer = TimerPage()
    stats = StatsPage()
    tasks = TaskPage()
    settings = SettingsPage()

    # Add pages to stack
    window.add_page(dashboard)   # 0: Dashboard
    window.add_page(timer)       # 1: Timer
    window.add_page(stats)       # 2: Statistics
    window.add_page(tasks)       # 3: Tasks
    window.add_page(settings)    # 4: Settings

    # ---------- Keyboard shortcuts ----------
    from PyQt6.QtGui import QShortcut, QKeySequence

    # Space = play/pause timer (only on timer page)
    space_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), window)
    space_shortcut.activated.connect(lambda: _toggle_timer(timer))

    # Escape = stop timer
    esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), window)
    esc_shortcut.activated.connect(lambda: _stop_timer(timer))

    # Ctrl+1-5 = switch pages
    for i in range(5):
        shortcut = QShortcut(QKeySequence(f"Ctrl+{i + 1}"), window)
        shortcut.activated.connect(lambda idx=i: _go_page(window, idx))

    window.show()
    sys.exit(app.exec())


def _switch_to_timer(window: MainWindow):
    window.sidebar.set_active(1)
    window.stack.setCurrentIndex(1)


def _toggle_timer(timer_page: TimerPage):
    """Toggle play/pause on the timer."""
    from app.core.timer_engine import TimerState
    if timer_page.timer_engine.state == TimerState.RUNNING:
        timer_page.timer_engine.pause()
    else:
        timer_page._on_play()


def _stop_timer(timer_page: TimerPage):
    """Stop the timer."""
    from app.core.timer_engine import TimerState
    if timer_page.timer_engine.state != TimerState.IDLE:
        timer_page._on_stop()


def _go_page(window: MainWindow, index: int):
    window.sidebar.set_active(index)
    window.stack.setCurrentIndex(index)


if __name__ == "__main__":
    main()