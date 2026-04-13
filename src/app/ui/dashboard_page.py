# src/app/ui/dashboard_page.py
"""Dashboard / home page — today's summary, quick start, timeline, sessions."""

from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core import dday_manager, session_manager
from app.core.timer_engine import TimerEngine
from app.ui.widgets.dday_card import DDayCard
from app.ui.widgets.session_card import SessionCard
from app.ui.widgets.timeline_bar import TimelineBar


class DashboardPage(QWidget):
    """Home page with today's summary, timeline, sessions, and D-Day cards."""

    # Signal to switch to timer page with the given subject
    quick_start_requested = None  # will be set after import to avoid circular

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        self._main_layout = QVBoxLayout(content)
        self._main_layout.setContentsMargins(40, 30, 40, 30)
        self._main_layout.setSpacing(24)

        # ---------- Header ----------
        header = QHBoxLayout()
        today_str = date.today().strftime("%A, %B %d")

        greeting = QLabel(f"📖  {today_str}")
        greeting.setProperty("class", "heading")
        header.addWidget(greeting)
        header.addStretch()

        self._main_layout.addLayout(header)

        # ---------- Stats Row ----------
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)

        # Today's study time
        self._today_card = self._make_stat_card("Today's Study", "0h 0m", "#6C5CE7")
        stats_row.addWidget(self._today_card)

        # Sessions count
        self._sessions_count_card = self._make_stat_card("Sessions", "0", "#00CEC9")
        stats_row.addWidget(self._sessions_count_card)

        # Quick start button card
        quick_card = QFrame()
        quick_card.setProperty("class", "card")
        quick_layout = QVBoxLayout(quick_card)
        quick_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._quick_btn = QPushButton("▶  Quick Start")
        self._quick_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._quick_btn.setStyleSheet("font-size: 16px; padding: 14px 28px;")
        quick_layout.addWidget(self._quick_btn)

        stats_row.addWidget(quick_card)
        self._main_layout.addLayout(stats_row)

        # ---------- Timeline ----------
        timeline_section = QVBoxLayout()
        timeline_header = QLabel("Today's Timeline")
        timeline_header.setProperty("class", "subheading")
        timeline_section.addWidget(timeline_header)

        self._timeline = TimelineBar()
        timeline_section.addWidget(self._timeline)
        self._main_layout.addLayout(timeline_section)

        # ---------- D-Day Events ----------
        self._dday_section = QVBoxLayout()
        dday_header = QHBoxLayout()
        dday_title = QLabel("D-Day Countdown")
        dday_title.setProperty("class", "subheading")
        dday_header.addWidget(dday_title)
        dday_header.addStretch()
        self._dday_section.addLayout(dday_header)

        self._dday_container = QHBoxLayout()
        self._dday_container.setSpacing(12)
        self._dday_container.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._dday_section.addLayout(self._dday_container)
        self._main_layout.addLayout(self._dday_section)

        # ---------- Today's Sessions ----------
        sessions_header = QHBoxLayout()
        sessions_title = QLabel("Today's Sessions")
        sessions_title.setProperty("class", "subheading")
        sessions_header.addWidget(sessions_title)
        sessions_header.addStretch()

        self._session_count_label = QLabel("0 sessions")
        self._session_count_label.setProperty("class", "muted")
        sessions_header.addWidget(self._session_count_label)
        self._main_layout.addLayout(sessions_header)

        self._sessions_container = QVBoxLayout()
        self._sessions_container.setSpacing(8)
        self._sessions_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._main_layout.addLayout(self._sessions_container)

        self._main_layout.addStretch()

        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _make_stat_card(self, title: str, value: str, accent: str) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)

        val_label = QLabel(value)
        val_label.setObjectName(f"stat_{title.lower().replace(' ', '_')}")
        val_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {accent};")
        layout.addWidget(val_label)

        title_label = QLabel(title)
        title_label.setProperty("class", "caption")
        layout.addWidget(title_label)

        return card

    def refresh(self):
        """Reload all dashboard data."""
        today = date.today()
        sessions = session_manager.get_sessions_for_date(today)
        total_seconds = sum(s.duration_seconds for s in sessions)

        # Update stat cards
        today_val = self._today_card.findChild(QLabel, "stat_today's_study")
        if today_val:
            today_val.setText(TimerEngine.format_seconds_short(total_seconds))

        count_label = self._sessions_count_card.findChild(QLabel, "stat_sessions")
        if count_label:
            count_label.setText(str(len(sessions)))

        # Update session count
        self._session_count_label.setText(f"{len(sessions)} sessions")

        # Refresh timeline
        self._timeline.set_date(today)

        # Refresh D-Day cards
        self._clear_layout(self._dday_container)
        events = dday_manager.list_upcoming_events()
        if events:
            for evt in events[:5]:  # Show max 5
                card = DDayCard(evt)
                self._dday_container.addWidget(card)
        else:
            empty = QLabel("No upcoming events")
            empty.setProperty("class", "muted")
            self._dday_container.addWidget(empty)

        # Refresh session list
        self._clear_layout(self._sessions_container)
        if sessions:
            for s in reversed(sessions):  # Newest first
                card = SessionCard(s)
                card.deleted.connect(self._on_session_deleted)
                self._sessions_container.addWidget(card)
        else:
            empty = QLabel("No sessions yet today. Start studying!")
            empty.setProperty("class", "muted")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("padding: 20px;")
            self._sessions_container.addWidget(empty)

    def _on_session_deleted(self, session_id: int):
        session_manager.delete_session(session_id)
        self.refresh()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()
