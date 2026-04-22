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
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.core import dday_manager, session_manager, subject_manager
from app.core.update_manager import CURRENT_VERSION, get_update_manager
from app.data.database import DB_PATH
from app.data.models import DDayEvent, Subject
from app.data.settings_store import load_setting, save_setting
from app.ui.contact_dialog import ContactDialog
from app.ui.widgets.report_dialog import ReportDialog


class CollapsibleSection(QWidget):
    """A collapsible section with a toggle button and content area."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._is_expanded = False
        self._setup_ui(title)

    def _setup_ui(self, title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toggle button
        self._toggle_btn = QPushButton(f"▶ {title}")
        self._toggle_btn.setProperty("class", "collapsible-btn")
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.setStyleSheet(
            """
            QPushButton {
                text-align: left;
                padding: 12px 16px;
                background-color: #2A2A3A;
                border: 1px solid #3A3A50;
                border-radius: 8px;
                color: #EAEAF0;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3A3A50;
            }
            """
        )
        self._toggle_btn.clicked.connect(self._toggle)
        layout.addWidget(self._toggle_btn)

        # Content container
        self._content = QWidget()
        self._content.setVisible(False)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(12, 12, 12, 12)
        self._content_layout.setSpacing(8)
        layout.addWidget(self._content)

    def _toggle(self):
        self._is_expanded = not self._is_expanded
        self._content.setVisible(self._is_expanded)
        text = self._toggle_btn.text()
        if self._is_expanded:
            self._toggle_btn.setText(text.replace("▶", "▼"))
        else:
            self._toggle_btn.setText(text.replace("▼", "▶"))

    def add_widget(self, widget):
        """Add a widget to the collapsible content area."""
        self._content_layout.addWidget(widget)

    def add_layout(self, layout):
        """Add a layout to the collapsible content area."""
        self._content_layout.addLayout(layout)


class SettingsPage(QWidget):
    """Settings page: subject CRUD, D-Day management, data export/reset."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # Main vertical layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # ---------- Header Bar (consistent with other pages) ----------
        header = QWidget()
        header.setObjectName("pageHeader")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(16)

        title = QLabel("Settings")
        title.setProperty("class", "heading")
        header_layout.addWidget(title)
        header_layout.addStretch()
        outer_layout.addWidget(header)

        # Horizontal separator line below header (aligned with sidebar profile level)
        horizontal_line = QFrame()
        horizontal_line.setObjectName("headerSeparator")
        horizontal_line.setFrameShape(QFrame.Shape.HLine)
        horizontal_line.setFixedHeight(1)
        outer_layout.addWidget(horizontal_line)

        # ---------- Content with Splitter ----------
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ========== LEFT PANEL: Settings Content ==========
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        # ========== Subject Management (Collapsible) ==========
        self._subjects_section = CollapsibleSection("Subjects")

        self._subjects_container = QVBoxLayout()
        self._subjects_container.setSpacing(8)
        self._subjects_section.add_layout(self._subjects_container)

        add_subject_btn = QPushButton("+ Add Subject")
        add_subject_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_subject_btn.clicked.connect(self._add_subject)
        self._subjects_section.add_widget(add_subject_btn)

        layout.addWidget(self._subjects_section)

        # ========== D-Day Events (Collapsible) ==========
        self._dday_section = CollapsibleSection("D-Day Events")

        self._dday_container = QVBoxLayout()
        self._dday_container.setSpacing(8)
        self._dday_section.add_layout(self._dday_container)

        add_dday_btn = QPushButton("+ Add Event")
        add_dday_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_dday_btn.clicked.connect(self._add_dday)
        self._dday_section.add_widget(add_dday_btn)

        layout.addWidget(self._dday_section)

        # ========== Data Management (Compact) ==========
        data_frame = QFrame()
        data_frame.setProperty("class", "card")
        data_layout = QVBoxLayout(data_frame)
        data_layout.setContentsMargins(16, 12, 16, 12)
        data_layout.setSpacing(8)

        data_header = QLabel("📦 Data")
        data_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #EAEAF0;")
        data_layout.addWidget(data_header)

        db_info = QLabel(f"Database: {DB_PATH}")
        db_info.setProperty("class", "caption")
        db_info.setWordWrap(True)
        data_layout.addWidget(db_info)

        data_btns = QHBoxLayout()
        data_btns.setSpacing(8)

        export_btn = QPushButton("📥 Export CSV")
        export_btn.setProperty("class", "secondary")
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self._export_csv)
        data_btns.addWidget(export_btn)

        reset_btn = QPushButton("🗑️ Reset")
        reset_btn.setProperty("class", "danger-btn")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_data)
        data_btns.addWidget(reset_btn)

        data_btns.addStretch()
        data_layout.addLayout(data_btns)

        layout.addWidget(data_frame)

        # ========== About & Update (Compact) ==========
        about_frame = QFrame()
        about_frame.setProperty("class", "card")
        about_layout = QVBoxLayout(about_frame)
        about_layout.setContentsMargins(16, 12, 16, 12)
        about_layout.setSpacing(8)

        about_header = QLabel(f"About — v{CURRENT_VERSION}")
        about_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #EAEAF0;")
        about_layout.addWidget(about_header)

        about = QLabel("Cygnus — A Yeolpumta-inspired study timer.\nBuilt with Python, PyQt6, and SQLModel.")
        about.setProperty("class", "muted")
        about_layout.addWidget(about)

        update_row = QHBoxLayout()
        update_row.setSpacing(8)

        self._check_update_btn = QPushButton("🔍 Check for Update")
        self._check_update_btn.setProperty("class", "secondary")
        self._check_update_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._check_update_btn.clicked.connect(self._check_for_update)
        update_row.addWidget(self._check_update_btn)

        self._update_status = QLabel("")
        self._update_status.setStyleSheet("font-size: 12px; color: #8B8BA0;")
        update_row.addWidget(self._update_status)
        update_row.addStretch()

        about_layout.addLayout(update_row)

        # Contact & Feedback buttons
        feedback_row = QHBoxLayout()
        feedback_row.setSpacing(8)

        contact_btn = QPushButton("📧 Contact Us")
        contact_btn.setProperty("class", "secondary")
        contact_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        contact_btn.clicked.connect(self._open_contact)
        feedback_row.addWidget(contact_btn)

        report_btn = QPushButton("🐛 Send Feedback")
        report_btn.setProperty("class", "secondary")
        report_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        report_btn.clicked.connect(self._open_report)
        feedback_row.addWidget(report_btn)

        feedback_row.addStretch()
        about_layout.addLayout(feedback_row)

        layout.addWidget(about_frame)

        layout.addStretch()

        scroll.setWidget(content)
        splitter.addWidget(scroll)

        # ========== RIGHT PANEL: Notice Board Sidebar ==========
        self._notice_sidebar = QWidget()
        self._notice_sidebar.setMinimumWidth(300)
        self._notice_sidebar.setMaximumWidth(400)
        notice_layout = QVBoxLayout(self._notice_sidebar)
        notice_layout.setContentsMargins(0, 0, 0, 0)
        notice_layout.setSpacing(8)

        # Sidebar header with toggle button
        header = QHBoxLayout()
        header.setContentsMargins(8, 0, 8, 0)

        notice_title = QLabel("📋 Update Notices")
        notice_title.setProperty("class", "subheading")
        header.addWidget(notice_title)
        header.addStretch()

        # Collapse/expand button
        self._toggle_btn = QPushButton("→")
        self._toggle_btn.setFixedSize(28, 28)
        self._toggle_btn.setProperty("class", "icon-btn")
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.setToolTip("Collapse notice board")
        self._toggle_btn.clicked.connect(self._toggle_notice_sidebar)
        header.addWidget(self._toggle_btn)

        notice_layout.addLayout(header)

        # Notice content scroll area
        notice_scroll = QScrollArea()
        notice_scroll.setWidgetResizable(True)
        notice_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        notice_content = QWidget()
        notice_content_layout = QVBoxLayout(notice_content)
        notice_content_layout.setContentsMargins(12, 0, 12, 12)
        notice_content_layout.setSpacing(12)
        notice_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Notice cards
        self._add_notice_card(
            notice_content_layout,
            "� v2.1.0 Released",
            "Cygnus v2.1.0 is now available! This update includes bug fixes and improvements. Check the About section below for details on how to update."
        )

        self._add_notice_card(
            notice_content_layout,
            "� Report Image UI Fixed",
            "The report image generation interface has been improved and is now working correctly."
        )

        self._add_notice_card(
            notice_content_layout,
            "� Check for Updates",
            "The update feature has been enhanced for better reliability. You can check for updates from the About section below."
        )

        self._add_notice_card(
            notice_content_layout,
            "💬 Send Feedback",
            "If you encounter any problems, use the report section to send bug reports and suggestions directly to us."
        )


        notice_content_layout.addStretch()
        notice_scroll.setWidget(notice_content)
        notice_layout.addWidget(notice_scroll)

        splitter.addWidget(self._notice_sidebar)
        splitter.setSizes([700, 300])
        splitter.setCollapsible(1, False)

        content_layout.addWidget(splitter, stretch=1)

        # Collapsed state button (shown when sidebar is hidden)
        self._expand_btn = QPushButton("←")
        self._expand_btn.setFixedSize(32, 32)
        self._expand_btn.setProperty("class", "icon-btn")
        self._expand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._expand_btn.setToolTip("Show notice board")
        self._expand_btn.clicked.connect(self._toggle_notice_sidebar)
        self._expand_btn.hide()
        content_layout.addWidget(self._expand_btn, alignment=Qt.AlignmentFlag.AlignTop)

        outer_layout.addWidget(content_widget, stretch=1)

    def _add_notice_card(self, layout, title: str, content: str):
        """Add a notice card to the notice board."""
        card = QFrame()
        card.setProperty("class", "card")
        card.setStyleSheet("""
            QFrame {
                background-color: #252535;
                border-radius: 8px;
                border-left: 3px solid #6C5CE7;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #EAEAF0;")
        card_layout.addWidget(title_lbl)

        content_lbl = QLabel(content)
        content_lbl.setStyleSheet("font-size: 12px; color: #A6ACCD; line-height: 1.4;")
        content_lbl.setWordWrap(True)
        card_layout.addWidget(content_lbl)

        layout.addWidget(card)

    def _toggle_notice_sidebar(self):
        """Toggle notice sidebar visibility."""
        if self._notice_sidebar.isVisible():
            self._notice_sidebar.hide()
            self._expand_btn.show()
        else:
            self._notice_sidebar.show()
            self._expand_btn.hide()

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

    def _check_for_update(self):
        """Check for application updates from GitHub."""
        self._check_update_btn.setEnabled(False)
        self._check_update_btn.setText("Checking...")
        self._update_status.setText("Checking GitHub for updates...")

        update_manager = get_update_manager()
        worker = update_manager.check_for_update(self)
        
        # Reset button state when check completes (success or error)
        worker.finished.connect(self._reset_update_button)

    def _reset_update_button(self):
        """Reset the check update button to default state."""
        self._check_update_btn.setEnabled(True)
        self._check_update_btn.setText("🔍 Check for Update")
        self._update_status.setText("")

    def _open_contact(self):
        """Open the contact us dialog."""
        dialog = ContactDialog(self)
        dialog.exec()

    def _open_report(self):
        """Open the report issue dialog."""
        dialog = ReportDialog(self)
        dialog.exec()

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
