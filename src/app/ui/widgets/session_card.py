# src/app/ui/widgets/session_card.py
"""Compact session display card with subject color, time range, and delete."""

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from app.core import subject_manager
from app.core.timer_engine import TimerEngine
from app.data.models import StudySession


class SessionCard(QFrame):
    """A compact card showing one study session."""

    deleted = pyqtSignal(int)  # session_id

    def __init__(self, study_session: StudySession, parent=None):
        super().__init__(parent)
        self._session = study_session
        self.setProperty("class", "card")
        self._setup_ui()

    def _setup_ui(self):
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(12)

        subj = subject_manager.get_subject(self._session.subject_id)
        color = subj.color_hex if subj else "#6C5CE7"

        # Color dot
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color}; font-size: 16px;")
        dot.setFixedWidth(20)
        row.addWidget(dot)

        # Subject name
        name = QLabel(subj.name if subj else "Unknown")
        name.setStyleSheet("font-weight: bold; font-size: 13px;")
        row.addWidget(name)

        # Time range
        start = self._session.start_time.strftime("%H:%M")
        end = self._session.end_time.strftime("%H:%M")
        time_label = QLabel(f"{start} – {end}")
        time_label.setProperty("class", "muted")
        time_label.setStyleSheet("font-size: 12px; color: #8B8BA0;")
        row.addWidget(time_label)

        row.addStretch()

        # Duration
        dur = QLabel(TimerEngine.format_seconds(self._session.duration_seconds))
        dur.setStyleSheet("font-family: 'Consolas', monospace; font-size: 13px;")
        row.addWidget(dur)

        # Delete button (hidden by default, shown on hover)
        self._del_btn = QPushButton("✕")
        self._del_btn.setProperty("class", "icon-btn")
        self._del_btn.setFixedSize(24, 24)
        self._del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._del_btn.setToolTip("Delete session")
        self._del_btn.setStyleSheet("color: #FF6B6B; font-size: 12px;")
        self._del_btn.clicked.connect(lambda: self.deleted.emit(self._session.id))
        row.addWidget(self._del_btn)
