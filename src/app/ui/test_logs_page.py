"""Test Tracker page for students to track their test scores (Coming Soon)."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class TestLogsPage(QWidget):
    """Test tracker page for students to track their test scores (Coming Soon)."""

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

        title = QLabel("Test Tracker")
        title.setProperty("class", "heading")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Coming soon label
        coming_soon = QLabel("(Coming Soon)")
        coming_soon.setStyleSheet("color: #8888A0; font-size: 13px;")
        header_layout.addWidget(coming_soon)

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
        self._main_layout.setContentsMargins(20, 20, 20, 20)
        self._main_layout.setSpacing(16)

        # Coming soon message
        coming_soon_label = QLabel("📝 Test Score Tracking")
        coming_soon_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #E0E0E0; margin-top: 40px;")
        coming_soon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._main_layout.addWidget(coming_soon_label)

        description = QLabel("Track your test scores and monitor your progress over time.\n\nThis feature is coming soon!")
        description.setStyleSheet("font-size: 14px; color: #8888A0; margin-top: 16px;")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._main_layout.addWidget(description)

        self._main_layout.addStretch()

        scroll.setWidget(content)
        outer_layout.addWidget(scroll, stretch=1)

