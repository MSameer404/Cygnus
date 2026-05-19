# src/app/ui/main_window.py
"""Main application window with sidebar navigation and stacked pages."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from app.ui.widgets.sidebar import Sidebar
from app.ui.profile_dialog import ProfileDialog


class _CentralWidget(QWidget):
    """Central container widget that paints the background image if set."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bg_pixmap = None

    def set_bg_pixmap(self, pixmap):
        self._bg_pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        if self._bg_pixmap:
            painter = QPainter(self)
            painter.drawPixmap(0, 0, self.width(), self.height(), self._bg_pixmap)
            painter.end()
        else:
            super().paintEvent(event)


class MainWindow(QMainWindow):
    """Top-level window: sidebar on the left, page stack on the right."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cygnus")
        self.setMinimumSize(1000, 700)
        self.resize(1100, 750)

        # Central container — uses custom widget so we can paint bg image
        self._central = _CentralWidget()
        self._central.setObjectName("centralContainer")
        self.setCentralWidget(self._central)

        layout = QHBoxLayout(self._central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        layout.addWidget(self.sidebar)

        # Vertical separator line between sidebar and content
        vertical_line = QFrame()
        vertical_line.setObjectName("sidebarSeparator")
        vertical_line.setFrameShape(QFrame.Shape.VLine)
        vertical_line.setFixedWidth(1)
        layout.addWidget(vertical_line)

        # Page stack
        self.stack = QStackedWidget()
        self.stack.setObjectName("contentArea")
        layout.addWidget(self.stack, stretch=1)

        # Connect sidebar navigation
        self.sidebar.page_changed.connect(self._switch_page)
        self.sidebar.profile_clicked.connect(self._open_profile)

    def add_page(self, page: QWidget):
        """Add a page to the stack (order must match Sidebar.PAGES)."""
        self.stack.addWidget(page)

    def _switch_page(self, index: int):
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)

    def load_stylesheet(self):
        """Load and apply the global QSS theme."""
        from app.core.utils import get_assets_dir
        qss_path = get_assets_dir() / "theme.qss"
        if qss_path.exists():
            self.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    def reload_background(self):
        """
        Build and apply the background pixmap.
        When a background image is active:
          - override the centralContainer's solid-color QSS paint so the image shows through
          - set the pixmap on the custom central widget
        """
        from app.core import background_manager as bm

        if bm.is_bg_enabled():
            px = bm.build_background_pixmap(self._central.width(), self._central.height())
            self._central.set_bg_pixmap(px)
            # Make centralContainer transparent so our paintEvent is visible
            self._central.setStyleSheet(
                "QWidget#centralContainer { background-color: transparent; }"
            )
            self.stack.setStyleSheet(
                "QWidget#contentArea { background-color: transparent; }"
            )
        else:
            self._central.set_bg_pixmap(None)
            # Restore original opaque background from QSS
            self._central.setStyleSheet("")
            self.stack.setStyleSheet("")

    def resizeEvent(self, event):
        """Rebuild background pixmap when the window is resized."""
        super().resizeEvent(event)
        from app.core import background_manager as bm
        if bm.is_bg_enabled() and self._central._bg_pixmap is not None:
            px = bm.build_background_pixmap(self._central.width(), self._central.height())
            self._central.set_bg_pixmap(px)

    def _open_profile(self):
        """Open the user profile dialog."""
        dialog = ProfileDialog(self)
        dialog.exec()
