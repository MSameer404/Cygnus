# src/app/ui/timer_page.py
"""Full-screen timer view with play/pause/stop controls and collapsible session sidebar."""

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
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.core.timer_engine import TimerEngine
from app.core import session_manager, subject_manager
from app.core.events import app_events
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
        app_events.data_reset.connect(self._on_data_reset)

    def _on_data_reset(self):
        """Reset timer state and refresh when all data is reset."""
        # Stop timer if running
        if self.timer_engine.state.value != 'idle':
            self.timer_engine.reset()
        self._current_subject = None
        self.subject_picker.refresh()
        self._refresh_sessions()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(0)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ========== LEFT PANEL: Timer ==========
        left_panel = QWidget()
        left_panel.setMinimumWidth(500)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 10, 20, 10)
        left_layout.setSpacing(0)

        # ---------- Subject Picker ----------
        self.subject_picker = SubjectPicker()
        left_layout.addWidget(self.subject_picker)
        left_layout.addSpacing(40)

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

        left_layout.addWidget(timer_container)
        left_layout.addSpacing(30)

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

        left_layout.addLayout(controls)
        left_layout.addSpacing(24)

        # ---------- Today's Total ----------
        self._today_label = QLabel("Today: 0h 0m")
        self._today_label.setProperty("class", "caption")
        self._today_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._today_label.setStyleSheet("font-size: 16px; color: #8B8BA0;")
        left_layout.addWidget(self._today_label)
        left_layout.addStretch()

        splitter.addWidget(left_panel)

        # ========== RIGHT PANEL: Sessions Sidebar ==========
        self._sidebar = QWidget()
        self._sidebar.setMinimumWidth(280)
        self._sidebar.setMaximumWidth(400)
        sidebar_layout = QVBoxLayout(self._sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(8)

        # Sidebar header with toggle button
        header = QHBoxLayout()
        header.setContentsMargins(8, 0, 8, 0)

        sessions_title = QLabel("Today's Sessions")
        sessions_title.setProperty("class", "subheading")
        header.addWidget(sessions_title)
        header.addStretch()

        add_session_btn = QPushButton("＋")
        add_session_btn.setFixedSize(28, 28)
        add_session_btn.setProperty("class", "icon-btn")
        add_session_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_session_btn.setToolTip("Add session")
        add_session_btn.clicked.connect(self._open_manual_session)
        header.addWidget(add_session_btn)

        # Collapse/expand button
        self._toggle_btn = QPushButton("→")
        self._toggle_btn.setFixedSize(28, 28)
        self._toggle_btn.setProperty("class", "icon-btn")
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.setToolTip("Collapse sidebar")
        self._toggle_btn.clicked.connect(self._toggle_sidebar)
        header.addWidget(self._toggle_btn)

        sidebar_layout.addLayout(header)

        # Compact session list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._sessions_container = QWidget()
        self._sessions_layout = QVBoxLayout(self._sessions_container)
        self._sessions_layout.setContentsMargins(8, 0, 8, 0)
        self._sessions_layout.setSpacing(6)
        self._sessions_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self._sessions_container)
        sidebar_layout.addWidget(scroll)

        splitter.addWidget(self._sidebar)
        splitter.setSizes([700, 300])
        splitter.setCollapsible(1, False)

        main_layout.addWidget(splitter, stretch=1)

        # Collapsed state button (shown when sidebar is hidden)
        self._expand_btn = QPushButton("←")
        self._expand_btn.setFixedSize(32, 32)
        self._expand_btn.setProperty("class", "icon-btn")
        self._expand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._expand_btn.setToolTip("Show sessions")
        self._expand_btn.clicked.connect(self._toggle_sidebar)
        self._expand_btn.hide()
        main_layout.addWidget(self._expand_btn, alignment=Qt.AlignmentFlag.AlignTop)

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
        self.subject_picker.refresh()

    def _on_tick(self, elapsed: int):
        self._timer_label.setText(TimerEngine.format_seconds(elapsed))

    def _on_state_changed(self, state: str):
        if state == "running":
            self._play_btn.hide()
            self._pause_btn.show()
            self._stop_btn.setEnabled(True)
            self.subject_picker.set_interactive(False)
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
            self.subject_picker.set_interactive(True)
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
        """Create a compact session card widget with color accent."""
        card = QFrame()
        card.setProperty("class", "card")
        main_layout = QHBoxLayout(card)
        main_layout.setContentsMargins(0, 0, 8, 0)
        main_layout.setSpacing(0)

        # Get subject info
        subj = subject_manager.get_subject(study_session.subject_id)
        color = subj.color_hex if subj else "#6C5CE7"

        # Left color accent bar
        accent_bar = QWidget()
        accent_bar.setFixedWidth(4)
        accent_bar.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
        main_layout.addWidget(accent_bar)

        # Content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 8, 0, 8)
        content_layout.setSpacing(4)

        # Subject name (top)
        name = QLabel(subj.name if subj else "Unknown")
        name.setStyleSheet("font-weight: bold; font-size: 13px; color: #EAEAF0;")
        content_layout.addWidget(name)

        # Time range (bottom)
        start_str = study_session.start_time.strftime("%H:%M")
        end_str = study_session.end_time.strftime("%H:%M")
        time_label = QLabel(f"{start_str} – {end_str}")
        time_label.setStyleSheet("font-size: 11px; color: #8B8BA0;")
        content_layout.addWidget(time_label)

        main_layout.addWidget(content, stretch=1)

        # Right side: duration and delete button
        right_side = QWidget()
        right_layout = QHBoxLayout(right_side)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Duration
        dur = QLabel(TimerEngine.format_seconds(study_session.duration_seconds))
        dur.setStyleSheet("font-family: 'Consolas', monospace; font-size: 13px; color: #EAEAF0;")
        right_layout.addWidget(dur)

        # Delete button (red, vertically centered)
        del_btn = QPushButton("×")
        del_btn.setFixedSize(24, 24)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setToolTip("Delete session")
        del_btn.setStyleSheet(
            "background-color: #FF6B6B; color: #FFFFFF; border: none; "
            "border-radius: 4px; font-size: 16px; font-weight: bold;"
        )
        del_btn.clicked.connect(lambda: self._delete_session(study_session.id))
        right_layout.addWidget(del_btn)

        main_layout.addWidget(right_side, alignment=Qt.AlignmentFlag.AlignVCenter)

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
            self.subject_picker.refresh()

    def _open_manual_session(self):
        from app.ui.widgets.manual_session_dialog import ManualSessionDialog
        dialog = ManualSessionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_sessions()
            self.subject_picker.refresh()

    def showEvent(self, event):
        """Refresh sessions when page becomes visible."""
        super().showEvent(event)
        self._refresh_sessions()
        self.subject_picker.refresh()

    def _toggle_sidebar(self):
        """Toggle sidebar visibility."""
        if self._sidebar.isVisible():
            self._sidebar.hide()
            self._expand_btn.show()
        else:
            self._sidebar.show()
            self._expand_btn.hide()
