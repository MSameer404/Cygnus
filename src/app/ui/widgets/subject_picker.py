# src/app/ui/widgets/subject_picker.py
"""Horizontal scrollable subject selector with color-coded cards."""

from datetime import date

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QWidget,
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QLabel,
    QColorDialog,
    QMenu,
)

from app.core import subject_manager, session_manager
from app.core.timer_engine import TimerEngine
from app.data.models import Subject
from app.ui.widgets.subject_card import SubjectCard


class SubjectPicker(QWidget):
    """Horizontal row of subject cards. Emits subject_selected(Subject)."""

    subject_selected = pyqtSignal(object)  # Subject or None
    subjects_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_id: int | None = None
        self._setup_ui()

    def _setup_ui(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFixedHeight(85)

        self._container = QWidget()
        self._layout = QHBoxLayout(self._container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(8)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self._container)
        outer.addWidget(scroll)

        self.refresh()

    def refresh(self):
        """Reload subjects from DB and rebuild cards."""
        # Clear existing
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        subjects = subject_manager.list_subjects()

        for subj in subjects:
            # Get today's study time for this subject
            today_seconds = session_manager.get_total_seconds_for_subject_on_date(subj.id, date.today())
            time_text = TimerEngine.format_seconds_short(today_seconds) if today_seconds > 0 else "0m"

            card = SubjectCard(subj.id, subj.name, subj.color_hex, time_text)
            card.setProperty("class", "subject-card")
            is_sel = subj.id == self._selected_id
            card.setProperty("selected", "true" if is_sel else "false")
            card.clicked.connect(lambda s=subj: self._select(s))
            card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            card.customContextMenuRequested.connect(
                lambda pos, s=subj, c=card: self._show_context_menu(s, c, pos)
            )
            self._layout.addWidget(card)

        # "+" button
        add_btn = QPushButton("+")
        add_btn.setProperty("class", "subject-card-add")
        add_btn.setFixedSize(50, 75)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setToolTip("Add subject")
        add_btn.clicked.connect(self._add_subject_dialog)
        self._layout.addWidget(add_btn)

        # Auto-select first if none selected
        if self._selected_id is None and subjects:
            self._select(subjects[0])

    def _select(self, subject: Subject):
        self._selected_id = subject.id
        self.subject_selected.emit(subject)
        # Update card visuals
        for i in range(self._layout.count()):
            w = self._layout.itemAt(i).widget()
            if w and isinstance(w, SubjectCard):
                is_this = w.subject_id == subject.id
                w.setProperty("selected", "true" if is_this else "false")
                w.style().unpolish(w)
                w.style().polish(w)

    def _show_context_menu(self, subject: Subject, card: SubjectCard, pos):
        menu = QMenu(self)
        edit_action = menu.addAction("✏️ Edit")
        delete_action = menu.addAction("🗑️ Delete")

        action = menu.exec(card.mapToGlobal(pos))
        if action == edit_action:
            self._edit_subject_dialog(subject)
        elif action == delete_action:
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.warning(
                self,
                "Delete Subject",
                f"Are you sure you want to delete '{subject.name}'?\n\nThis action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                subject_manager.delete_subject(subject.id)
                if self._selected_id == subject.id:
                    self._selected_id = None
                self.refresh()
                self.subjects_changed.emit()

    def _add_subject_dialog(self):
        dialog = SubjectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, color = dialog.get_values()
            if name:
                subject_manager.create_subject(name, color)
                self.refresh()
                self.subjects_changed.emit()

    def _edit_subject_dialog(self, subject: Subject):
        dialog = SubjectDialog(self, subject)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, color = dialog.get_values()
            if name:
                subject_manager.update_subject(subject.id, name, color)
                self.refresh()
                self.subjects_changed.emit()

    @property
    def selected_subject_id(self) -> int | None:
        return self._selected_id

    def set_interactive(self, enabled: bool):
        """Enable or disable card interaction (for when timer is running)."""
        self.setEnabled(enabled)
        # Update visual opacity
        if enabled:
            self.setStyleSheet("")
        else:
            self.setStyleSheet("opacity: 0.6;")


class SubjectDialog(QDialog):
    """Dialog for creating or editing a subject."""

    PRESET_COLORS = [
        "#6C5CE7", "#00CEC9", "#FF6B6B", "#FDCB6E",
        "#E17055", "#74B9FF", "#A29BFE", "#55EFC4",
        "#FF7675", "#FD79A8", "#636E72", "#2D3436",
    ]

    def __init__(self, parent=None, subject: Subject | None = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Subject" if subject else "New Subject")
        self.setFixedSize(360, 280)
        self._color = subject.color_hex if subject else "#6C5CE7"

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Name input
        layout.addWidget(QLabel("Subject Name"))
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("e.g., Biology")
        if subject:
            self._name_input.setText(subject.name)
        layout.addWidget(self._name_input)

        # Color picker
        layout.addWidget(QLabel("Color"))
        color_row = QHBoxLayout()
        color_row.setSpacing(6)
        for c in self.PRESET_COLORS:
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {c}; "
                f"border: 2px solid transparent; "
                f"border-radius: 14px; }}"
                f"QPushButton:hover {{ border-color: #EAEAF0; }}"
            )
            btn.clicked.connect(lambda checked, col=c: self._set_color(col))
            color_row.addWidget(btn)

        # Custom color button
        custom_btn = QPushButton("...")
        custom_btn.setFixedSize(28, 28)
        custom_btn.setToolTip("Custom color")
        custom_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        custom_btn.clicked.connect(self._pick_custom_color)
        color_row.addWidget(custom_btn)
        layout.addLayout(color_row)

        # Preview
        self._preview = QLabel("● Preview")
        self._preview.setStyleSheet(f"color: {self._color}; font-size: 18px;")
        layout.addWidget(self._preview, alignment=Qt.AlignmentFlag.AlignCenter)

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

    def _set_color(self, color: str):
        self._color = color
        self._preview.setStyleSheet(f"color: {color}; font-size: 18px;")

    def _pick_custom_color(self):
        color = QColorDialog.getColor(QColor(self._color), self)
        if color.isValid():
            self._set_color(color.name())

    def get_values(self) -> tuple[str, str]:
        return self._name_input.text().strip(), self._color
