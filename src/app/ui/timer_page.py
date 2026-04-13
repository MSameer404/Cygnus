# src/app/ui/timer_page.py
"""Full-screen timer view with play/pause/stop controls and session list."""

from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core.timer_engine import TimerEngine
from app.core import session_manager, subject_manager
from app.data.models import Subject
from app.ui.widgets.subject_picker import SubjectPicker


class TimerPage(QWidget):
    """Page with a large timer display, controls, and today's session list."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_subject: Subject | None = None

        self.timer_engine = TimerEngine(self)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(0)

        # ---------- Subject Picker ----------
        self.subject_picker = SubjectPicker()
        layout.addWidget(self.subject_picker)
        layout.addSpacing(40)

        # ---------- Timer Display ----------
        timer_container = QWidget()
        timer_layout = QVBoxLayout(timer_container)
        timer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.setSpacing(8)

        self._timer_label = QLabel("00:00:00")
        self._timer_label.setProperty("class", "timer-display")
        self._timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.addWidget(self._timer_label)

        # Status label
        self._status_label = QLabel("Ready to study")
        self._status_label.setProperty("class", "muted")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.addWidget(self._status_label)

        layout.addWidget(timer_container)
        layout.addSpacing(30)

        # ---------- Controls ----------
        controls = QHBoxLayout()
        controls.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls.setSpacing(20)

        self._play_btn = QPushButton("▶")
        self._play_btn.setProperty("class", "play-btn")
        self._play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._play_btn.setToolTip("Start / Resume")
        controls.addWidget(self._play_btn)

        self._pause_btn = QPushButton("⏸")
        self._pause_btn.setProperty("class", "play-btn")
        self._pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pause_btn.setToolTip("Pause")
        self._pause_btn.hide()
        controls.addWidget(self._pause_btn)

        self._stop_btn = QPushButton("⏹")
        self._stop_btn.setProperty("class", "stop-btn")
        self._stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._stop_btn.setToolTip("Stop & Save")
        self._stop_btn.setEnabled(False)
        controls.addWidget(self._stop_btn)

        layout.addLayout(controls)
        layout.addSpacing(24)

        # ---------- Today's Total ----------
        self._today_label = QLabel("Today: 0h 0m")
        self._today_label.setProperty("class", "caption")
        self._today_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._today_label.setStyleSheet("font-size: 16px; color: #8B8BA0;")
        layout.addWidget(self._today_label)
        layout.addSpacing(20)

        # ---------- Today's Sessions ----------
        sessions_header = QHBoxLayout()
        sessions_title = QLabel("Today's Sessions")
        sessions_title.setProperty("class", "subheading")
        sessions_header.addWidget(sessions_title)
        sessions_header.addStretch()

        add_session_btn = QPushButton("＋ Add Session")
        add_session_btn.setProperty("class", "secondary")
        add_session_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_session_btn.setToolTip("Manually record a past study session")
        add_session_btn.clicked.connect(self._open_manual_session)
        sessions_header.addWidget(add_session_btn)

        layout.addLayout(sessions_header)
        layout.addSpacing(8)

        # Session list in scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._sessions_container = QWidget()
        self._sessions_layout = QVBoxLayout(self._sessions_container)
        self._sessions_layout.setContentsMargins(0, 0, 0, 0)
        self._sessions_layout.setSpacing(8)
        self._sessions_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self._sessions_container)
        layout.addWidget(scroll, stretch=1)

    def _connect_signals(self):
        self.subject_picker.subject_selected.connect(self._on_subject_selected)
        self.timer_engine.tick.connect(self._on_tick)
        self.timer_engine.state_changed.connect(self._on_state_changed)
        self._play_btn.clicked.connect(self._on_play)
        self._pause_btn.clicked.connect(self._on_pause)
        self._stop_btn.clicked.connect(self._on_stop)

    def _on_subject_selected(self, subject: Subject):
        self._current_subject = subject

    def _on_play(self):
        if self._current_subject is None:
            self._status_label.setText("⚠ Select a subject first")
            return
        self.timer_engine.start()

    def _on_pause(self):
        self.timer_engine.pause()

    def _on_stop(self):
        start, end, duration = self.timer_engine.stop()
        if start and duration > 0 and self._current_subject:
            session_manager.save_session(
                subject_id=self._current_subject.id,
                start_time=start,
                end_time=end,
                duration_seconds=duration,
            )
        self._refresh_sessions()

    def _on_tick(self, elapsed: int):
        self._timer_label.setText(TimerEngine.format_seconds(elapsed))

    def _on_state_changed(self, state: str):
        if state == "running":
            self._play_btn.hide()
            self._pause_btn.show()
            self._stop_btn.setEnabled(True)
            self._status_label.setText(
                f"Studying: {self._current_subject.name}" if self._current_subject else "Studying..."
            )
            self._status_label.setStyleSheet("font-size: 14px; color: #00CEC9;")
        elif state == "paused":
            self._pause_btn.hide()
            self._play_btn.show()
            self._play_btn.setText("▶")
            self._status_label.setText("Paused")
            self._status_label.setStyleSheet("font-size: 14px; color: #FDCB6E;")
        else:  # idle
            self._pause_btn.hide()
            self._play_btn.show()
            self._play_btn.setText("▶")
            self._stop_btn.setEnabled(False)
            self._timer_label.setText("00:00:00")
            self._status_label.setText("Ready to study")
            self._status_label.setStyleSheet("font-size: 14px; color: #8B8BA0;")

    def _refresh_sessions(self):
        """Reload today's sessions from DB."""
        # Clear existing
        while self._sessions_layout.count():
            item = self._sessions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        sessions = session_manager.get_sessions_for_date(date.today())
        total = sum(s.duration_seconds for s in sessions)
        self._today_label.setText(f"Today: {TimerEngine.format_seconds_short(total)}")

        if not sessions:
            empty = QLabel("No sessions yet today. Start studying!")
            empty.setProperty("class", "muted")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._sessions_layout.addWidget(empty)
            return

        for s in reversed(sessions):  # newest first
            card = self._make_session_card(s)
            self._sessions_layout.addWidget(card)

    def _make_session_card(self, study_session) -> QFrame:
        """Create a compact session card widget."""
        card = QFrame()
        card.setProperty("class", "card")
        row = QHBoxLayout(card)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(12)

        # Color dot
        subj = subject_manager.get_subject(study_session.subject_id)
        color = subj.color_hex if subj else "#6C5CE7"
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color}; font-size: 16px;")
        dot.setFixedWidth(20)
        row.addWidget(dot)

        # Subject name
        name = QLabel(subj.name if subj else "Unknown")
        name.setStyleSheet("font-weight: bold;")
        row.addWidget(name)

        # Time range
        start_str = study_session.start_time.strftime("%H:%M")
        end_str = study_session.end_time.strftime("%H:%M")
        time_label = QLabel(f"{start_str} – {end_str}")
        time_label.setProperty("class", "muted")
        row.addWidget(time_label)

        row.addStretch()

        # Duration
        dur = QLabel(TimerEngine.format_seconds(study_session.duration_seconds))
        dur.setStyleSheet("font-family: 'Consolas', monospace; color: #EAEAF0;")
        row.addWidget(dur)

        # Delete button
        del_btn = QPushButton("✕")
        del_btn.setProperty("class", "icon-btn")
        del_btn.setFixedSize(28, 28)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setToolTip("Delete session")
        del_btn.clicked.connect(lambda: self._delete_session(study_session.id))
        row.addWidget(del_btn)

        return card

    def _delete_session(self, session_id: int):
        reply = QMessageBox.warning(
            self,
            "Delete Session",
            "Are you sure you want to delete this study session?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            session_manager.delete_session(session_id)
            self._refresh_sessions()

    def _open_manual_session(self):
        from app.ui.widgets.manual_session_dialog import ManualSessionDialog
        dialog = ManualSessionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_sessions()

    def showEvent(self, event):
        """Refresh sessions when page becomes visible."""
        super().showEvent(event)
        self._refresh_sessions()
