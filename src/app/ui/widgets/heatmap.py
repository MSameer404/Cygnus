# src/app/ui/widgets/heatmap.py
"""GitHub-style study heatmap calendar widget."""

import calendar
from datetime import date, timedelta

from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QColor, QPainter, QFont, QPainterPath
from PyQt6.QtWidgets import QWidget, QToolTip

from app.core.timer_engine import TimerEngine


class HeatmapWidget(QWidget):
    """Year-view heatmap showing study intensity per day."""

    CELL_SIZE = 14
    CELL_GAP = 3
    DAY_LABELS = ["Mon", "", "Wed", "", "Fri", "", "Sun"]

    # Color scale from no study to max study
    COLORS = [
        "#1A1A24",  # 0 hours
        "#2A2545",  # < 1 hour
        "#3D3570",  # < 2 hours
        "#5A4BD6",  # < 4 hours
        "#6C5CE7",  # < 6 hours
        "#7F71EF",  # 6+ hours
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: dict[date, int] = {}
        self._year = date.today().year
        self.setMouseTracking(True)
        self.setMinimumHeight(self.CELL_SIZE * 7 + self.CELL_GAP * 6 + 50)

    def set_data(self, data: dict[date, int], year: int | None = None):
        """Set heatmap data: {date: seconds}."""
        self._data = data
        if year is not None:
            self._year = year
        self.update()

    def _get_color(self, seconds: int) -> QColor:
        """Map seconds studied to a color intensity."""
        hours = seconds / 3600
        if hours == 0:
            return QColor(self.COLORS[0])
        elif hours < 1:
            return QColor(self.COLORS[1])
        elif hours < 2:
            return QColor(self.COLORS[2])
        elif hours < 4:
            return QColor(self.COLORS[3])
        elif hours < 6:
            return QColor(self.COLORS[4])
        else:
            return QColor(self.COLORS[5])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        x_offset = 40  # Space for day labels
        y_offset = 24  # Space for month labels
        cell = self.CELL_SIZE
        gap = self.CELL_GAP

        # Day labels
        painter.setPen(QColor("#8B8BA0"))
        painter.setFont(QFont("Segoe UI", 8))
        for i, label in enumerate(self.DAY_LABELS):
            if label:
                y = y_offset + i * (cell + gap) + cell / 2 + 4
                painter.drawText(0, int(y), label)

        # Draw cells week by week
        start = date(self._year, 1, 1)
        current = start

        col = 0
        last_month = -1

        is_current_year = (
            current.year == self._year
        )
        while is_current_year or current <= date(self._year, 12, 31):
            if current > date(self._year, 12, 31):
                break

            row = current.weekday()  # 0=Mon, 6=Sun
            x = x_offset + col * (cell + gap)
            y = y_offset + row * (cell + gap)

            seconds = self._data.get(current, 0)
            color = self._get_color(seconds)

            path = QPainterPath()
            path.addRoundedRect(QRectF(x, y, cell, cell), 3, 3)
            painter.fillPath(path, color)

            # Month label at the start of each month
            if current.month != last_month and current.day <= 7:
                painter.setPen(QColor("#8B8BA0"))
                painter.setFont(QFont("Segoe UI", 8))
                month_name = calendar.month_abbr[current.month]
                painter.drawText(int(x), int(y_offset - 6), month_name)
                last_month = current.month

            # Move to next day
            if row == 6:  # Sunday, move to next column
                col += 1
            current += timedelta(days=1)

        painter.end()

    def mouseMoveEvent(self, event):
        """Show tooltip with date and study time."""
        pos = event.position() if hasattr(event, 'position') else event.pos()

        x_offset = 40
        y_offset = 24
        cell = self.CELL_SIZE
        gap = self.CELL_GAP

        col = int((pos.x() - x_offset) / (cell + gap))
        row = int((pos.y() - y_offset) / (cell + gap))

        if 0 <= row <= 6 and col >= 0:
            # Calculate date from col/row
            start = date(self._year, 1, 1)
            offset = row - start.weekday()
            target = start + timedelta(weeks=col, days=offset)

            if target.year == self._year:
                seconds = self._data.get(target, 0)
                dur = TimerEngine.format_seconds_short(seconds)
                fmt = target.strftime('%b %d, %Y')
                text = f"{fmt}\n{dur} studied"
                global_pos = event.globalPosition().toPoint()
                QToolTip.showText(global_pos, text)
                return

        QToolTip.hideText()
