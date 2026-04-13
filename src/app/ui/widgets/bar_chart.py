# src/app/ui/widgets/bar_chart.py
"""Vertical bar chart for daily/weekly/monthly study time visualization."""

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QPainterPath, QLinearGradient
from PyQt6.QtWidgets import QWidget

from app.core.timer_engine import TimerEngine


class BarChart(QWidget):
    """Vertical bar chart with gradient bars and axis labels."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._values: list[int] = []  # seconds
        self._labels: list[str] = []
        self._accent = "#6C5CE7"
        self._highlight_index: int | None = None
        self.setMinimumHeight(200)
        self.setMouseTracking(True)

    def set_data(self, values: list[int], labels: list[str], accent: str = "#6C5CE7"):
        """Set bar data. values=seconds, labels=x-axis labels."""
        self._values = values
        self._labels = labels
        self._accent = accent
        self.update()

    def paintEvent(self, event):
        if not self._values:
            painter = QPainter(self)
            painter.setPen(QPen(QColor("#8B8BA0")))
            painter.setFont(QFont("Segoe UI", 12))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data")
            painter.end()
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        padding_left = 50
        padding_right = 20
        padding_top = 20
        padding_bottom = 40

        chart_w = self.width() - padding_left - padding_right
        chart_h = self.height() - padding_top - padding_bottom

        max_val = max(self._values) if self._values else 1
        if max_val == 0:
            max_val = 3600  # Default 1 hour scale

        n = len(self._values)
        bar_total_w = chart_w / max(n, 1)
        bar_w = min(bar_total_w * 0.6, 40)
        gap = (bar_total_w - bar_w) / 2

        # Y-axis gridlines
        painter.setPen(QPen(QColor("#252535"), 1))
        painter.setFont(QFont("Segoe UI", 9))
        num_gridlines = 5
        for i in range(num_gridlines + 1):
            y = padding_top + chart_h - (i / num_gridlines) * chart_h
            painter.drawLine(padding_left, int(y), self.width() - padding_right, int(y))

            # Y-axis label
            val = int((i / num_gridlines) * max_val)
            label = TimerEngine.format_seconds_short(val)
            painter.setPen(QPen(QColor("#8B8BA0")))
            painter.drawText(
                QRectF(0, y - 8, padding_left - 8, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                label,
            )
            painter.setPen(QPen(QColor("#252535"), 1))

        # Bars
        accent_color = QColor(self._accent)
        for i, val in enumerate(self._values):
            x = padding_left + i * bar_total_w + gap
            bar_h = (val / max_val) * chart_h if max_val > 0 else 0
            y = padding_top + chart_h - bar_h

            # Gradient bar
            gradient = QLinearGradient(x, y, x, padding_top + chart_h)
            gradient.setColorAt(0, accent_color)
            gradient.setColorAt(1, QColor(
                accent_color.red(),
                accent_color.green(),
                accent_color.blue(), 100,
            ))

            bar_rect = QRectF(x, y, bar_w, bar_h)
            path = QPainterPath()
            path.addRoundedRect(bar_rect, 4, 4)

            if i == self._highlight_index:
                painter.fillPath(path, accent_color.lighter(130))
            else:
                painter.fillPath(path, gradient)

            # X-axis label
            if i < len(self._labels):
                painter.setPen(QPen(QColor("#8B8BA0")))
                painter.setFont(QFont("Segoe UI", 9))
                label_rect = QRectF(
                    x - gap,
                    padding_top + chart_h + 8,
                    bar_total_w, 20,
                )
                painter.drawText(
                    label_rect,
                    Qt.AlignmentFlag.AlignCenter,
                    self._labels[i],
                )

        painter.end()

    def mouseMoveEvent(self, event):
        """Highlight bar on hover."""
        pos = event.position() if hasattr(event, 'position') else event.pos()
        x = pos.x()

        padding_left = 50
        padding_right = 20
        chart_w = self.width() - padding_left - padding_right
        n = len(self._values)

        if n > 0 and padding_left <= x <= self.width() - padding_right:
            bar_total_w = chart_w / n
            idx = int((x - padding_left) / bar_total_w)
            if 0 <= idx < n:
                self._highlight_index = idx
            else:
                self._highlight_index = None
        else:
            self._highlight_index = None

        self.update()

    def leaveEvent(self, event):
        self._highlight_index = None
        self.update()
