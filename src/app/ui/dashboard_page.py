# src/app/ui/dashboard_page.py
"""Dashboard / home page — today's summary, quick start, timeline, sessions."""

from pathlib import Path
import json
import random
from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core import dday_manager, session_manager, stats_engine
from app.core.events import app_events
from app.core.timer_engine import TimerEngine
from app.ui.widgets.dday_card import DDayCard
from app.ui.widgets.timeline_bar import TimelineBar


class DashboardPage(QWidget):
    """Home page with today's summary, timeline, sessions, and D-Day cards."""

    # Signal to switch to timer page with the given subject
    quick_start_requested = None  # will be set after import to avoid circular

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        app_events.data_reset.connect(self._on_data_reset)

    def _on_data_reset(self):
        """Refresh dashboard when all data is reset."""
        self.refresh()

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

        # Streak card
        self._streak_card = self._make_stat_card("Streak", "0 days", "#FDCB6E")
        stats_row.addWidget(self._streak_card)

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

        # ---------- Motivation ----------
        motivation_header = QHBoxLayout()
        motivation_title = QLabel("Daily Motivation")
        motivation_title.setProperty("class", "subheading")
        motivation_header.addWidget(motivation_title)
        motivation_header.addStretch()
        self._main_layout.addLayout(motivation_header)

        motivation_card = QFrame()
        motivation_card.setProperty("class", "card")
        self._motivation_layout = QVBoxLayout(motivation_card)
        self._motivation_layout.setContentsMargins(24, 24, 24, 24)
        
        self._quote_label = QLabel("Loading quote...")
        self._quote_label.setWordWrap(True)
        self._quote_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._quote_label.setStyleSheet("font-size: 18px; font-style: italic; color: #E0E0E0;")
        
        self._author_label = QLabel("")
        self._author_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._author_label.setProperty("class", "caption")
        self._author_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #A0A0A0; margin-top: 10px;")

        self._motivation_layout.addWidget(self._quote_label)
        self._motivation_layout.addWidget(self._author_label)

        self._main_layout.addWidget(motivation_card)

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

        # Update streak
        streak_label = self._streak_card.findChild(QLabel, "stat_streak")
        if streak_label:
            streak = stats_engine.get_streak()
            streak_label.setText(f"{streak} day{'s' if streak != 1 else ''}")

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

        # Show Daily Motivation quote
        self._refresh_quote()

    def _refresh_quote(self):
        try:
            quotes_path = Path(__file__).parent.parent / "data" / "quotes.json"
            if quotes_path.exists():
                with open(quotes_path, "r", encoding="utf-8") as f:
                    quotes = json.load(f)
                if quotes:
                    q = random.choice(quotes)
                    self._quote_label.setText(f'"{q["text"]}"')
                    self._author_label.setText(f"— {q['author']}")
                    return
        except Exception as e:
            print(f"Error loading quotes: {e}")
            
        self._quote_label.setText('"Success is the sum of small efforts, repeated day in and day out."')
        self._author_label.setText("— Robert Collier")

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()
