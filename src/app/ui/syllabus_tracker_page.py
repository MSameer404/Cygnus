# src/app/ui/syllabus_tracker_page.py
"""Syllabus Tracker page — for tracking academic syllabus progress."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class SyllabusTrackerPage(QWidget):
    """Syllabus tracker page for monitoring academic progress."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # ---------- Header Bar ----------
        header = QWidget()
        header.setObjectName("pageHeader")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(16)

        title = QLabel("Syllabus Tracker")
        title.setProperty("class", "heading")
        header_layout.addWidget(title)
        header_layout.addStretch()

        outer_layout.addWidget(header)

        # Horizontal separator line below header
        horizontal_line = QFrame()
        horizontal_line.setObjectName("headerSeparator")
        horizontal_line.setFrameShape(QFrame.Shape.HLine)
        horizontal_line.setFixedHeight(1)
        outer_layout.addWidget(horizontal_line)

        # ---------- Scrollable Content ----------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        self._main_layout = QVBoxLayout(content)
        self._main_layout.setContentsMargins(40, 30, 40, 30)
        self._main_layout.setSpacing(24)

        # Placeholder content
        placeholder = QLabel("Syllabus Tracker - Coming Soon")
        placeholder.setProperty("class", "muted")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._main_layout.addWidget(placeholder)

        self._main_layout.addStretch()

        scroll.setWidget(content)
        outer_layout.addWidget(scroll, stretch=1)

    def refresh(self):
        """Refresh the page data."""
        pass

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()
