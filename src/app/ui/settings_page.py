# src/app/ui/settings_page.py
"""Settings page with subject management, D-Day events, and data options."""

import csv
import os
from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QColorDialog,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core import dday_manager, session_manager, subject_manager
from app.data.database import DB_PATH
from app.data.models import DDayEvent, Subject


class SettingsPage(QWidget):
    """Settings page: subject CRUD, D-Day management, data export/reset."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(24)

        # ---------- Header ----------
        title = QLabel("Settings")
        title.setProperty("class", "heading")
        layout.addWidget(title)

        # ========== Subject Management ==========
        layout.addWidget(self._section_label("Subjects"))

        self._subjects_container = QVBoxLayout()
        self._subjects_container.setSpacing(8)
        layout.addLayout(self._subjects_container)

        add_subject_btn = QPushButton("+ Add Subject")
        add_subject_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_subject_btn.clicked.connect(self._add_subject)
        layout.addWidget(add_subject_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self._add_separator(layout)

        # ========== D-Day Events ==========
        layout.addWidget(self._section_label("D-Day Events"))

        self._dday_container = QVBoxLayout()
        self._dday_container.setSpacing(8)
        layout.addLayout(self._dday_container)

        add_dday_btn = QPushButton("+ Add Event")
        add_dday_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_dday_btn.clicked.connect(self._add_dday)
        layout.addWidget(add_dday_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self._add_separator(layout)

        # ========== Data Management ==========
        layout.addWidget(self._section_label("Data"))

        data_row = QHBoxLayout()
        data_row.setSpacing(12)

        # Database location
        db_info = QLabel(f"📁 Database: {DB_PATH}")
        db_info.setProperty("class", "caption")
        db_info.setWordWrap(True)
        layout.addWidget(db_info)

        export_btn = QPushButton("📥 Export Sessions (CSV)")
        export_btn.setProperty("class", "secondary")
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self._export_csv)
        data_row.addWidget(export_btn)

        reset_btn = QPushButton("🗑️ Reset All Data")
        reset_btn.setProperty("class", "danger-btn")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_data)
        data_row.addWidget(reset_btn)

        data_row.addStretch()
        layout.addLayout(data_row)

        self._add_separator(layout)

        # ========== About ==========
        layout.addWidget(self._section_label("About"))
        about = QLabel("Cygnus (Beta v1) — A Yeolpumta-inspired study timer.\nBuilt with Python, PyQt6, and SQLModel.")
        about.setProperty("class", "muted")
        layout.addWidget(about)

        layout.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setProperty("class", "subheading")
        return label

    def _add_separator(self, layout):
        sep = QFrame()
        sep.setProperty("class", "separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

    # ---------- Subject Management ----------

    def _refresh_subjects(self):
        while self._subjects_container.count():
            item = self._subjects_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for subj in subject_manager.list_subjects():
            card = QFrame()
            card.setProperty("class", "card")
            row = QHBoxLayout(card)
            row.setContentsMargins(12, 8, 12, 8)
            row.setSpacing(12)

            dot = QLabel("●")
            dot.setStyleSheet(f"color: {subj.color_hex}; font-size: 18px;")
            dot.setFixedWidth(20)
            row.addWidget(dot)

            name = QLabel(subj.name)
            name.setStyleSheet("font-weight: bold;")
            row.addWidget(name, stretch=1)

            color_label = QLabel(subj.color_hex)
            color_label.setProperty("class", "caption")
            row.addWidget(color_label)

            edit_btn = QPushButton("✏️")
            edit_btn.setProperty("class", "icon-btn")
            edit_btn.setFixedSize(28, 28)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda checked, s=subj: self._edit_subject(s))
            row.addWidget(edit_btn)

            del_btn = QPushButton("✕")
            del_btn.setProperty("class", "icon-btn")
            del_btn.setFixedSize(28, 28)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet("color: #FF6B6B;")
            del_btn.clicked.connect(lambda checked, s=subj: self._delete_subject(s))
            row.addWidget(del_btn)

            self._subjects_container.addWidget(card)

    def _add_subject(self):
        from app.ui.widgets.subject_picker import SubjectDialog
        dialog = SubjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, color = dialog.get_values()
            if name:
                subject_manager.create_subject(name, color)
                self._refresh_subjects()

    def _edit_subject(self, subject: Subject):
        from app.ui.widgets.subject_picker import SubjectDialog
        dialog = SubjectDialog(self, subject)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, color = dialog.get_values()
            if name:
                subject_manager.update_subject(subject.id, name, color)
                self._refresh_subjects()

    def _delete_subject(self, subject: Subject):
        reply = QMessageBox.question(
            self,
            "Delete Subject",
            f"Delete '{subject.name}'? Sessions using this subject will keep their data.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            subject_manager.delete_subject(subject.id)
            self._refresh_subjects()

    # ---------- D-Day Management ----------

    def _refresh_dday(self):
        while self._dday_container.count():
            item = self._dday_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        events = dday_manager.list_events()
        if not events:
            empty = QLabel("No D-Day events yet.")
            empty.setProperty("class", "muted")
            self._dday_container.addWidget(empty)
            return

        for evt in events:
            card = QFrame()
            card.setProperty("class", "card")
            row = QHBoxLayout(card)
            row.setContentsMargins(12, 8, 12, 8)
            row.setSpacing(12)

            dot = QLabel("●")
            dot.setStyleSheet(f"color: {evt.color_hex}; font-size: 18px;")
            dot.setFixedWidth(20)
            row.addWidget(dot)

            name = QLabel(evt.title)
            name.setStyleSheet("font-weight: bold;")
            row.addWidget(name, stretch=1)

            days = dday_manager.get_days_remaining(evt)
            if days > 0:
                dday_text = f"D-{days}"
            elif days == 0:
                dday_text = "D-DAY"
            else:
                dday_text = f"D+{abs(days)}"

            dday_label = QLabel(dday_text)
            dday_label.setStyleSheet("font-weight: bold; color: #FDCB6E;")
            row.addWidget(dday_label)

            date_label = QLabel(evt.target_date.strftime("%Y-%m-%d"))
            date_label.setProperty("class", "caption")
            row.addWidget(date_label)

            del_btn = QPushButton("✕")
            del_btn.setProperty("class", "icon-btn")
            del_btn.setFixedSize(28, 28)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet("color: #FF6B6B;")
            del_btn.clicked.connect(lambda checked, e=evt: self._delete_dday(e))
            row.addWidget(del_btn)

            self._dday_container.addWidget(card)

    def _add_dday(self):
        dialog = DDayDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title, target, color = dialog.get_values()
            if title:
                dday_manager.create_event(title, target, color)
                self._refresh_dday()

    def _delete_dday(self, event: DDayEvent):
        reply = QMessageBox.warning(
            self,
            "Delete Event",
            f"Are you sure you want to delete the event '{event.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            dday_manager.delete_event(event.id)
            self._refresh_dday()

    # ---------- Data Management ----------

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Sessions", "pytp_sessions.csv", "CSV Files (*.csv)"
        )
        if not path:
            return

        sessions = session_manager.get_sessions_for_range(
            date(2000, 1, 1), date(2100, 1, 1)
        )

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Subject", "Start", "End", "Duration (s)", "Notes"])
            for s in sessions:
                subj = subject_manager.get_subject(s.subject_id)
                writer.writerow([
                    s.id,
                    subj.name if subj else "Unknown",
                    s.start_time.isoformat(),
                    s.end_time.isoformat(),
                    s.duration_seconds,
                    s.notes,
                ])

        QMessageBox.information(self, "Export Complete", f"Exported {len(sessions)} sessions to:\n{path}")

    def _reset_data(self):
        reply = QMessageBox.warning(
            self,
            "Reset All Data",
            "⚠ This will permanently delete ALL sessions, tasks, events, profile data, and settings.\n\nAre you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Double confirm
            reply2 = QMessageBox.critical(
                self,
                "Final Confirmation",
                "This action CANNOT be undone.\nProfile picture and all data will be lost.\n\nProceed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply2 == QMessageBox.StandardButton.Yes:
                # Reset all data and notify other pages
                from app.core.data_reset import reset_all_data
                from app.core.events import app_events

                reset_all_data()
                self._refresh_subjects()
                self._refresh_dday()

                # Notify all other pages to refresh
                app_events.data_reset.emit()

                QMessageBox.information(self, "Reset Complete", "All data has been reset. The app is now fresh.")

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_subjects()
        self._refresh_dday()


class DDayDialog(QDialog):
    """Dialog for creating a D-Day event."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New D-Day Event")
        self.setFixedSize(360, 260)
        self._color = "#FDCB6E"

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # Title
        layout.addWidget(QLabel("Event Name"))
        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("e.g., Final Exam")
        layout.addWidget(self._title_input)

        # Date
        layout.addWidget(QLabel("Target Date"))
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(date.today())
        self._date_edit.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(self._date_edit)

        # Color
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Color"))
        self._color_preview = QPushButton()
        self._color_preview.setFixedSize(28, 28)
        self._color_preview.setStyleSheet(
            f"background-color: {self._color}; border: none; border-radius: 14px;"
        )
        self._color_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self._color_preview.clicked.connect(self._pick_color)
        color_row.addWidget(self._color_preview)
        color_row.addStretch()
        layout.addLayout(color_row)

        # Buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "ghost")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._color), self)
        if color.isValid():
            self._color = color.name()
            self._color_preview.setStyleSheet(
                f"background-color: {self._color}; border: none; border-radius: 14px;"
            )

    def get_values(self) -> tuple[str, date, str]:
        return (
            self._title_input.text().strip(),
            self._date_edit.date().toPyDate(),
            self._color,
        )
