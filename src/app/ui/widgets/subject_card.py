# src/app/ui/widgets/subject_card.py
"""Subject card widget with color accent and study time display."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QWidget


class SubjectCard(QFrame):
    """A card displaying subject name, today's study time, and color accent."""

    clicked = pyqtSignal()

    def __init__(self, subject_id: int, name: str, color_hex: str, today_time_text: str, parent=None):
        super().__init__(parent)
        self._subject_id = subject_id
        self._name = name
        self._color_hex = color_hex
        self._today_time_text = today_time_text
        self._setup_ui()

    def _setup_ui(self):
        self.setProperty("class", "subject-card")
        self.setFixedSize(130, 75)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Main horizontal layout: accent bar + content
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left colored accent bar
        accent_bar = QWidget()
        accent_bar.setFixedWidth(4)
        accent_bar.setStyleSheet(f"background-color: {self._color_hex}; border-radius: 2px;")
        main_layout.addWidget(accent_bar)

        # Content container
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 8, 10, 8)
        content_layout.setSpacing(4)

        # Subject name
        name_label = QLabel(self._name)
        name_label.setProperty("class", "subject-card-name")
        name_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #EAEAF0;")
        content_layout.addWidget(name_label)

        # Today's study time
        time_label = QLabel(self._today_time_text)
        time_label.setProperty("class", "subject-card-time")
        time_label.setStyleSheet("font-size: 11px; color: #8B8BA0;")
        content_layout.addWidget(time_label)

        content_layout.addStretch()
        main_layout.addWidget(content, stretch=1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def update_time(self, time_text: str):
        """Update the displayed study time."""
        self._today_time_text = time_text
        for child in self.findChildren(QLabel):
            if child.property("class") == "subject-card-time":
                child.setText(time_text)
                break

    @property
    def subject_id(self) -> int:
        return self._subject_id

    @property
    def subject_name(self) -> str:
        return self._name

    @property
    def color_hex(self) -> str:
        return self._color_hex
