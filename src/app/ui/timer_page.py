# src/app/ui/timer_page.py
"""Full-screen timer view with play/pause/stop controls and collapsible session sidebar."""

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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
        main_layout.setContentsMargins(20, 0, 20, 20)
        main_layout.setSpacing(0)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: rgba(255, 255, 255, 0.1);
                width: 1px;
            }
        """)

        # ========== LEFT PANEL: Timer ==========
        left_panel = QWidget()
        left_panel.setMinimumWidth(500)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(20, 0, 20, 10)
        left_layout.setSpacing(0)

        # ---------- Subject Picker ----------
        self.subject_picker = SubjectPicker()
        left_layout.addWidget(self.subject_picker)
        left_layout.addSpacing(40)

        # ---------- Timer Display ----------
        timer_container = QFrame()
        timer_container.setObjectName("timerContainer")
        timer_container.setStyleSheet("""
            QFrame#timerContainer {
                background-color: rgba(42, 44, 49, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 32px;
            }
        """)
        timer_layout = QVBoxLayout(timer_container)
        timer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.setContentsMargins(40, 50, 40, 50)
        timer_layout.setSpacing(16)

        self._timer_label = QLabel("00:00:00")
        self._timer_label.setStyleSheet("""
            font-size: 96px;
            font-family: 'Consolas', monospace;
            font-weight: bold;
            color: #ECFDF5;
            letter-spacing: 4px;
        """)
        self._timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.addWidget(self._timer_label)

        # Status label
        self._status_label = QLabel("Ready to study")
        self._status_label.setStyleSheet("font-size: 18px; color: #10B981; font-weight: 600; letter-spacing: 1px;")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_layout.addWidget(self._status_label)

        left_layout.addWidget(timer_container)
        left_layout.addSpacing(40)

        # ---------- Controls (Single Button) ----------
        controls = QHBoxLayout()
        controls.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._session_btn = QPushButton("▶  START")
        self._session_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._session_btn.setMinimumHeight(64)
        self._session_btn.setMinimumWidth(240)
        self._session_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #34D399);
                color: #ECFDF5;
                border-radius: 32px;
                font-size: 20px;
                font-weight: bold;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34D399, stop:1 #10B981);
                border: 2px solid #6EE7B7;
            }
        """)
        self._session_btn.clicked.connect(self._on_session_button_clicked)
        controls.addWidget(self._session_btn)

        left_layout.addLayout(controls)
        left_layout.addSpacing(32)

        # ---------- Today's Total ----------
        self._today_label = QLabel("Today: 0h 0m")
        self._today_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._today_label.setStyleSheet("""
            font-size: 16px;
            color: #10B981;
            font-weight: bold;
            background-color: rgba(16, 185, 129, 0.15);
            border-radius: 16px;
            padding: 8px 24px;
        """)
        
        today_layout = QHBoxLayout()
        today_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        today_layout.addWidget(self._today_label)
        left_layout.addLayout(today_layout)
        
        left_layout.addStretch()

        splitter.addWidget(left_panel)

        # ========== RIGHT PANEL: Sessions Sidebar ==========
        self._sidebar = QWidget()
        self._sidebar.setMinimumWidth(280)
        self._sidebar.setMaximumWidth(400)
        sidebar_layout = QVBoxLayout(self._sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(8)

        # Sidebar header
        header = QHBoxLayout()
        header.setContentsMargins(8, 16, 8, 16)
        header.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)

        header.addStretch()

        sessions_title = QLabel("Session History")
        sessions_title.setStyleSheet("""
            font-size: 16px; 
            font-weight: 600; 
            color: #ECFDF5; 
            letter-spacing: 0.5px;
        """)
        header.addWidget(sessions_title, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        header.addSpacing(16)

        add_session_btn = QPushButton("＋ Add")
        add_session_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_session_btn.setToolTip("Add session manually")
        add_session_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #10B981;
                border: 1px solid #065F46;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
                padding: 4px 12px 5px 12px;
            }
            QPushButton:hover {
                background-color: rgba(16, 185, 129, 0.15);
                color: #10B981;
                border-color: #10B981;
            }
            QPushButton:pressed {
                background-color: rgba(16, 185, 129, 0.25);
            }
        """)
        add_session_btn.clicked.connect(self._open_manual_session)
        header.addWidget(add_session_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        header.addStretch()

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



    def _connect_signals(self):
        self.subject_picker.subject_selected.connect(self._on_subject_selected)
        self.timer_engine.tick.connect(self._on_tick)
        self.timer_engine.state_changed.connect(self._on_state_changed)

    def _on_subject_selected(self, subject: Subject):
        self._current_subject = subject

    def _on_session_button_clicked(self):
        """Handle the single session button click with confirmations."""
        if not self.timer_engine.is_running:
            # Starting a session - require confirmation
            if self._current_subject is None:
                self._status_label.setText("⚠ Select a subject first")
                return

            reply = QMessageBox.question(
                self,
                "Start Session",
                f"Start studying <b>{self._current_subject.name}</b>?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.timer_engine.start()
        else:
            # Stopping a session - require confirmation
            elapsed = self.timer_engine.elapsed_seconds
            elapsed_str = TimerEngine.format_seconds(elapsed)

            reply = QMessageBox.question(
                self,
                "Stop & Save Session",
                f"Stop session and save <b>{elapsed_str}</b> of study time?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._stop_and_save()

    def _stop_and_save(self):
        """Stop timer and save the session (if at least 5 minutes)."""

        start, end, duration = self.timer_engine.stop()
        MIN_SESSION_SECONDS = 5 * 60  # 5 minutes

        if start and duration > 0 and self._current_subject:
            if duration < MIN_SESSION_SECONDS:
                # Session too short - discard without saving
                QMessageBox.information(
                    self,
                    "Session Too Short",
                    f"Session is too small to be counted in database.\n"
                    f"Duration: {TimerEngine.format_seconds(duration)}\n\n"
                    f"It should be at least 5 minutes to be saved.",
                )
            else:
                # Save valid session
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
            self._session_btn.setText("⏹  STOP & SAVE")
            self._session_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #34D399);
                    color: #ECFDF5;
                    border-radius: 32px;
                    font-size: 20px;
                    font-weight: bold;
                    letter-spacing: 2px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34D399, stop:1 #10B981);
                    border: 2px solid #FDA4AF;
                }
            """)
            self.subject_picker.set_interactive(False)
            self._status_label.setText(
                f"Studying: {self._current_subject.name}" if self._current_subject else "Studying..."
            )
            self._status_label.setStyleSheet("font-size: 18px; color: #10B981; font-weight: 600; letter-spacing: 1px;")
            self._timer_label.setStyleSheet("""
                font-size: 96px;
                font-family: 'Consolas', monospace;
                font-weight: bold;
                color: #10B981;
                letter-spacing: 4px;
            """)
        else:  # idle
            self._session_btn.setText("▶  START")
            self._session_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #34D399);
                    color: #ECFDF5;
                    border-radius: 32px;
                    font-size: 20px;
                    font-weight: bold;
                    letter-spacing: 2px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34D399, stop:1 #10B981);
                    border: 2px solid #6EE7B7;
                }
            """)
            self.subject_picker.set_interactive(True)
            self._timer_label.setText("00:00:00")
            self._timer_label.setStyleSheet("""
                font-size: 96px;
                font-family: 'Consolas', monospace;
                font-weight: bold;
                color: #ECFDF5;
                letter-spacing: 4px;
            """)
            self._status_label.setText("Ready to study")
            self._status_label.setStyleSheet("font-size: 18px; color: #10B981; font-weight: 600; letter-spacing: 1px;")

    def _refresh_sessions(self):
        """Reload recent sessions from DB."""
        # Clear existing
        while self._sessions_layout.count():
            item = self._sessions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Update Today's Total
        today_sessions = session_manager.get_sessions_for_date(date.today())
        total = sum(s.duration_seconds for s in today_sessions)
        self._today_label.setText(f"Today: {TimerEngine.format_seconds_short(total)}")

        # Fetch the last 10 sessions for history
        recent_sessions = session_manager.get_recent_sessions(limit=10)

        if not recent_sessions:
            empty = QLabel("No sessions yet. Start studying!")
            empty.setProperty("class", "muted")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._sessions_layout.addWidget(empty)
            return

        for s in recent_sessions:
            card = self._make_session_card(s)
            self._sessions_layout.addWidget(card)

    def _make_session_card(self, study_session) -> QFrame:
        """Create a compact session card widget with color accent."""
        card = QFrame()
        card.setProperty("class", "card")
        card.setStyleSheet("QFrame.card { padding: 8px; border-radius: 12px; }")
        
        main_layout = QHBoxLayout(card)
        main_layout.setContentsMargins(0, 0, 8, 0)
        main_layout.setSpacing(12)

        # Get subject info
        subj = subject_manager.get_subject(study_session.subject_id)
        color = subj.color_hex if subj else "#6C5CE7"

        # Left color accent bar
        accent_bar = QWidget()
        accent_bar.setFixedSize(6, 40)
        accent_bar.setStyleSheet(f"background-color: {color}; border-radius: 3px;")
        main_layout.addWidget(accent_bar)

        # Content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(4, 4, 0, 4)
        content_layout.setSpacing(4)

        # Subject name (top)
        name = QLabel(subj.name if subj else "Unknown")
        name.setStyleSheet("font-weight: bold; font-size: 14px; color: #ECFDF5;")
        content_layout.addWidget(name)

        # Time range (bottom)
        if study_session.start_time.date() == date.today():
            date_str = "Today"
        else:
            date_str = study_session.start_time.strftime("%b %d")
            
        start_str = study_session.start_time.strftime("%H:%M")
        end_str = study_session.end_time.strftime("%H:%M")
        time_label = QLabel(f"{date_str}, {start_str} – {end_str}")
        time_label.setStyleSheet("font-size: 12px; color: #6EE7B7; font-weight: 500;")
        content_layout.addWidget(time_label)

        main_layout.addWidget(content, stretch=1)

        # Right side: duration and delete button
        right_side = QWidget()
        right_layout = QHBoxLayout(right_side)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Duration
        dur = QLabel(TimerEngine.format_seconds(study_session.duration_seconds))
        dur.setStyleSheet("font-family: 'Consolas', monospace; font-size: 14px; font-weight: bold; color: #10B981;")
        right_layout.addWidget(dur)

        # Delete button
        del_btn = QPushButton("×")
        del_btn.setFixedSize(28, 28)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setToolTip("Delete session")
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6EE7B7;
                border: none;
                border-radius: 14px;
                font-size: 20px;
                font-weight: bold;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                background-color: rgba(255, 107, 107, 0.15);
                color: #FF6B6B;
            }
        """)
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


