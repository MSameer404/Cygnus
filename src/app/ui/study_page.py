"""Unified Study page with Timer/Stats toggle switch in header."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QButtonGroup,
)

from app.core.events import app_events
from app.ui.timer_page import TimerPage
from app.ui.stats_page import StatsPage


class StudyPage(QWidget):
    """Unified study page with toggle between Timer and Statistics views.
    
    Layout:
        ┌────────────────────────────────────────────────────────┐
        │  Study                       [Timer | Stats]           │  ← Header with toggle
        ├────────────────────────────────────────────────────────┤
        │                                                        │
        │  [Timer View]  or  [Statistics View]                    │  ← Stacked content
        │                                                        │
        └────────────────────────────────────────────────────────┘
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        app_events.data_reset.connect(self._on_data_reset)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---------- Header Bar ----------
        header = QWidget()
        header.setObjectName("studyHeader")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(16)

        # Title (left side, aligned with sidebar profile button level)
        title = QLabel("Time Tracker")
        title.setProperty("class", "heading")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Toggle switch (right side, same horizontal level as profile button)
        self._timer_btn = QPushButton("Timer")
        self._timer_btn.setCheckable(True)
        self._timer_btn.setProperty("class", "segment-btn")
        self._timer_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._timer_btn.setFixedWidth(70)

        self._stats_btn = QPushButton("Stats")
        self._stats_btn.setCheckable(True)
        self._stats_btn.setProperty("class", "segment-btn")
        self._stats_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._stats_btn.setFixedWidth(70)

        # Button group for exclusive selection
        self._toggle_group = QButtonGroup(self)
        self._toggle_group.setExclusive(True)
        self._toggle_group.addButton(self._timer_btn, 0)
        self._toggle_group.addButton(self._stats_btn, 1)
        self._toggle_group.buttonClicked.connect(self._on_toggle_changed)

        # Add buttons directly to header (no outer container/boundary)
        header_layout.addWidget(self._timer_btn)
        header_layout.addWidget(self._stats_btn)
        layout.addWidget(header)

        # Horizontal separator line below header (aligned with sidebar profile level)
        horizontal_line = QFrame()
        horizontal_line.setObjectName("headerSeparator")
        horizontal_line.setFrameShape(QFrame.Shape.HLine)
        horizontal_line.setFixedHeight(1)
        layout.addWidget(horizontal_line)

        # ---------- Content Stack ----------
        self._stack = QStackedWidget()
        self._stack.setObjectName("studyStack")

        # Timer view
        self._timer_view = TimerView()
        self._stack.addWidget(self._timer_view)

        # Stats view
        self._stats_view = StatsView()
        self._stack.addWidget(self._stats_view)

        layout.addWidget(self._stack, stretch=1)

        # Set initial state
        self._timer_btn.setChecked(True)
        self._stack.setCurrentIndex(0)

    def _on_toggle_changed(self, btn: QPushButton):
        """Switch between timer and stats views."""
        index = self._toggle_group.id(btn)
        self._stack.setCurrentIndex(index)

        # Refresh stats when switching to it
        if index == 1:
            self._stats_view.refresh()

    def _on_data_reset(self):
        """Refresh both views when data is reset."""
        self._timer_view.refresh()
        self._stats_view.refresh()


class TimerView(QWidget):
    """Timer view - extracted TimerPage UI without independent page wrapper."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Use the existing TimerPage as-is, but it's now embedded
        self._timer_page = TimerPage()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._timer_page)

    def refresh(self):
        """Refresh the timer view."""
        # Trigger the timer page's show event logic
        self._timer_page.showEvent(None)


class StatsView(QWidget):
    """Stats view - extracted StatsPage UI without independent page wrapper."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Use the existing StatsPage as-is, but it's now embedded
        self._stats_page = StatsPage()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stats_page)

    def refresh(self):
        """Refresh the stats view."""
        # Trigger the stats page's show event logic
        self._stats_page.showEvent(None)
