# src/app/ui/widgets/subject_card.py
"""Subject card widget with color accent and study time display."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QWidget


def hex_to_rgba(hex_str: str, alpha: float) -> str:
    """Convert hex color to rgba string for QSS."""
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join(c*2 for c in hex_str)
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


class SubjectCard(QFrame):
    """A card displaying subject name, today's study time, and color accent."""

    clicked = Signal()

    def __init__(self, subject_id: int, name: str, color_hex: str, today_time_text: str, parent=None):
        super().__init__(parent)
        self._subject_id = subject_id
        self._name = name
        self._color_hex = color_hex
        self._today_time_text = today_time_text
        self._setup_ui()

    def _setup_ui(self):
        self.setProperty("class", "subject-card")
        self.setFixedSize(160, 80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Generate custom styling based on subject's accent color
        rgba_bg_unsel = "rgba(30, 10, 35, 0.45)"
        rgba_bg_hover = "rgba(42, 14, 48, 0.65)"
        rgba_bg_sel = hex_to_rgba(self._color_hex, 0.16)
        
        rgba_border_unsel = hex_to_rgba(self._color_hex, 0.22)
        rgba_border_hover = hex_to_rgba(self._color_hex, 0.55)
        rgba_border_sel = self._color_hex

        self.setStyleSheet(f"""
            QFrame.subject-card {{
                background: {rgba_bg_unsel};
                border: 1px solid {rgba_border_unsel};
                border-radius: 14px;
            }}
            QFrame.subject-card:hover {{
                background: {rgba_bg_hover};
                border: 1.5px solid {rgba_border_hover};
            }}
            QFrame.subject-card[selected="true"] {{
                background: {rgba_bg_sel};
                border: 2px solid {rgba_border_sel};
            }}
            QWidget#accentContainer {{
                background: transparent;
                border: none;
            }}
            QLabel#subjectCardName {{
                font-weight: 600;
                font-size: 14px;
                color: #ECFDF5;
                letter-spacing: 0.3px;
                background: transparent;
                border: none;
            }}
            QFrame.subject-card[selected="true"] QLabel#subjectCardName {{
                color: #FFFFFF;
            }}
            QLabel#subjectCardTime {{
                font-size: 12px;
                color: #6EE7B7;
                font-weight: 500;
                background: transparent;
                border: none;
            }}
            QFrame.subject-card[selected="true"] QLabel#subjectCardTime {{
                color: #FFF0F5;
            }}
        """)

        # Main horizontal layout: accent bar + content
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left colored accent bar container for vertical padding/pill alignment
        accent_container = QWidget()
        accent_container.setObjectName("accentContainer")
        accent_layout = QVBoxLayout(accent_container)
        accent_layout.setContentsMargins(10, 14, 0, 14)
        accent_layout.setSpacing(0)

        accent_bar = QWidget()
        accent_bar.setObjectName("accentBar")
        accent_bar.setFixedWidth(5)
        accent_bar.setStyleSheet(f"background-color: {self._color_hex}; border-radius: 2.5px;")
        accent_layout.addWidget(accent_bar)
        main_layout.addWidget(accent_container)

        # Content container
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(4)

        # Subject name
        name_label = QLabel(self._name)
        name_label.setObjectName("subjectCardName")
        name_label.setProperty("class", "subject-card-name")
        content_layout.addWidget(name_label)

        # Today's study time
        time_label = QLabel(self._today_time_text)
        time_label.setObjectName("subjectCardTime")
        time_label.setProperty("class", "subject-card-time")
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
