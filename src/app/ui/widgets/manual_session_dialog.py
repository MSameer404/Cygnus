# src/app/ui/widgets/manual_session_dialog.py
"""Dialog for manually adding a past study session."""

from datetime import date, time

from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTimeEdit,
    QVBoxLayout,
)

from app.core import session_manager, subject_manager


class ManualSessionDialog(QDialog):
    """Dialog to manually record a study session that happened without the timer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Manual Session")
        self.setFixedSize(400, 380)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 20)

        # Header
        header = QLabel("📝 Record a Past Session")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #EAEAF0;")
        layout.addWidget(header)

        hint = QLabel("Didn't have your device? Log the session here.")
        hint.setStyleSheet("font-size: 12px; color: #8B8BA0;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addSpacing(4)

        # Subject
        layout.addWidget(self._make_label("Subject"))
        self._subject_combo = QComboBox()
        for s in subject_manager.list_subjects():
            self._subject_combo.addItem(f"● {s.name}", s.id)
        layout.addWidget(self._subject_combo)

        # Date
        layout.addWidget(self._make_label("Date"))
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setDisplayFormat("yyyy-MM-dd")
        self._date_edit.setMaximumDate(QDate.currentDate())
        layout.addWidget(self._date_edit)

        # Time range
        time_row = QHBoxLayout()
        time_row.setSpacing(12)

        start_col = QVBoxLayout()
        start_col.addWidget(self._make_label("Start Time"))
        self._start_time = QTimeEdit()
        self._start_time.setDisplayFormat("HH:mm")
        self._start_time.setTime(QTime(9, 0))
        start_col.addWidget(self._start_time)
        time_row.addLayout(start_col)

        end_col = QVBoxLayout()
        end_col.addWidget(self._make_label("End Time"))
        self._end_time = QTimeEdit()
        self._end_time.setDisplayFormat("HH:mm")
        self._end_time.setTime(QTime(10, 0))
        end_col.addWidget(self._end_time)
        time_row.addLayout(end_col)

        layout.addLayout(time_row)

        # Notes
        layout.addWidget(self._make_label("Notes (optional)"))
        self._notes_input = QLineEdit()
        self._notes_input.setPlaceholderText("e.g., Studied at library without laptop")
        layout.addWidget(self._notes_input)

        layout.addSpacing(8)

        # Error label (hidden by default)
        self._error_label = QLabel()
        self._error_label.setStyleSheet(
            "color: #FF6B6B; font-size: 12px; padding: 4px 8px; "
            "background-color: rgba(255, 107, 107, 0.1); border-radius: 4px;"
        )
        self._error_label.hide()
        layout.addWidget(self._error_label)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "ghost")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Save Session")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(
            "padding: 8px 18px; font-weight: bold;"
        )
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    @staticmethod
    def _make_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #B0B0C0;")
        return lbl

    def _save(self):
        subject_id = self._subject_combo.currentData()
        if subject_id is None:
            self._show_error("Please select a subject.")
            return

        session_date = self._date_edit.date().toPyDate()
        start_t = self._start_time.time().toPyTime()
        end_t = self._end_time.time().toPyTime()

        try:
            session_manager.add_manual_session(
                subject_id=subject_id,
                session_date=session_date,
                start_time=start_t,
                end_time=end_t,
                notes=self._notes_input.text().strip(),
            )
        except ValueError as e:
            self._show_error(str(e))
            return

        self.accept()

    def _show_error(self, message: str):
        self._error_label.setText(f"⚠ {message}")
        self._error_label.show()
