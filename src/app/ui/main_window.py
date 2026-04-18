# src/app/ui/main_window.py
"""Main application window with sidebar navigation and stacked pages."""

from pathlib import Path

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from app.ui.widgets.sidebar import Sidebar
from app.ui.profile_dialog import ProfileDialog
from app.ui.contact_dialog import ContactDialog
from app.ui.widgets.report_dialog import ReportDialog


class MainWindow(QMainWindow):
    """Top-level window: sidebar on the left, page stack on the right."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cygnus")
        self.setMinimumSize(1000, 700)
        self.resize(1100, 750)

        # Central container
        central = QWidget()
        central.setObjectName("centralContainer")
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        layout.addWidget(self.sidebar)

        # Page stack
        self.stack = QStackedWidget()
        self.stack.setObjectName("contentArea")
        layout.addWidget(self.stack, stretch=1)

        # Connect sidebar navigation
        self.sidebar.page_changed.connect(self._switch_page)
        self.sidebar.profile_clicked.connect(self._open_profile)
        self.sidebar.contact_clicked.connect(self._open_contact)
        self.sidebar.report_clicked.connect(self._open_report)

    def add_page(self, page: QWidget):
        """Add a page to the stack (order must match Sidebar.PAGES)."""
        self.stack.addWidget(page)

    def _switch_page(self, index: int):
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)

    def load_stylesheet(self):
        """Load and apply the global QSS theme."""
        qss_path = Path(__file__).parent.parent / "assets" / "theme.qss"
        if qss_path.exists():
            self.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    def _open_profile(self):
        """Open the user profile dialog."""
        dialog = ProfileDialog(self)
        dialog.exec()

    def _open_contact(self):
        """Open the contact us dialog."""
        dialog = ContactDialog(self)
        dialog.exec()

    def _open_report(self):
        """Open the report issue dialog."""
        dialog = ReportDialog(self)
        dialog.exec()
