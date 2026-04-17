# src/app/ui/widgets/create_task_dialog.py
"""Modal dialog for creating a new task."""

from datetime import date

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from app.core import subject_manager


class CreateTaskDialog(QDialog):
    """Collect title, subject, priority, and due date for a new task."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Create task")
        self.setModal(True)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._title = QLineEdit()
        self._title.setPlaceholderText("Task title")
        form.addRow("Title", self._title)

        self._subject = QComboBox()
        self._subject.addItem("No subject", None)
        for s in subject_manager.list_subjects():
            self._subject.addItem(s.name, s.id)
        form.addRow("Subject", self._subject)

        self._priority = QComboBox()
        self._priority.addItem("High", "high")
        self._priority.addItem("Med", "med")
        self._priority.addItem("Low", "low")
        self._priority.setCurrentIndex(1)
        form.addRow("Priority", self._priority)

        self._due = QDateEdit()
        self._due.setCalendarPopup(True)
        self._due.setDate(QDate.currentDate())
        self._due.setDisplayFormat("yyyy-MM-dd")
        form.addRow("Due date", self._due)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        if not self._title.text().strip():
            self._title.setFocus()
            return
        self.accept()

    def values(self) -> tuple[str, int | None, str, date]:
        """Return title, subject_id, priority key, due date."""
        qd = self._due.date()
        due = date(qd.year(), qd.month(), qd.day())
        return (
            self._title.text().strip(),
            self._subject.currentData(),
            self._priority.currentData(),
            due,
        )
