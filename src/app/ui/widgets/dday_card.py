# src/app/ui/widgets/dday_card.py
"""D-Day countdown card widget."""

from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel

from app.data.models import DDayEvent


class DDayCard(QFrame):
    """Compact card showing D-Day countdown for an event."""

    def __init__(self, event: DDayEvent, parent=None):
        super().__init__(parent)
        self._event = event
        self._accent = event.color_hex
        self.setProperty("class", "card")
        self.setFixedWidth(180)
        self.setMinimumHeight(90)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 12, 14, 12)
        layout.setSpacing(4)

        # Event title
        title = QLabel(self._event.title)
        title.setStyleSheet(
            "font-weight: bold; font-size: 13px; "
            "background: transparent;"
        )
        title.setWordWrap(True)
        layout.addWidget(title)

        # D-Day countdown
        days = (self._event.target_date - date.today()).days
        if days > 0:
            dday_text = f"D-{days}"
            color = "#FDCB6E" if days <= 7 else "#EAEAF0"
        elif days == 0:
            dday_text = "D-DAY"
            color = "#FF6B6B"
        else:
            dday_text = f"D+{abs(days)}"
            color = "#8B8BA0"

        dday_label = QLabel(dday_text)
        dday_label.setStyleSheet(
            f"font-size: 22px; font-weight: bold; "
            f"color: {color}; background: transparent;"
        )
        layout.addWidget(dday_label)

        # Date
        date_label = QLabel(
            self._event.target_date.strftime("%Y.%m.%d")
        )
        date_label.setStyleSheet(
            "font-size: 11px; color: #8B8BA0; "
            "background: transparent;"
        )
        layout.addWidget(date_label)

    def paintEvent(self, event):
        """Draw the card with a thick accent left-border."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw thick left accent bar
        accent = QColor(self._accent)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(accent)
        painter.drawRoundedRect(0, 4, 5, self.height() - 8, 2, 2)

        painter.end()
