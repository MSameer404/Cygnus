# src/app/ui/widgets/step_chart.py
"""Step-line chart for daily cumulative study time visualization."""

from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QColor, QPainter, QPen, QFont
from PyQt6.QtWidgets import QWidget


class StepChart(QWidget):
    """
    Step-line chart showing cumulative study time throughout the day.
    X-axis: hours (00-24)
    Y-axis: cumulative minutes studied
    Steps up when a session ends.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sessions: list[dict] = []  # List of dicts with start_time, end_time
        self._line_color = QColor("#6C5CE7")  # Purple accent
        self._grid_color = QColor("#252535")
        self._text_color = QColor("#8B8BA0")
        self._bg_color = QColor("#1A1A24")
        self.setMinimumHeight(250)

    def set_sessions(self, sessions: list[dict]):
        """
        Set session data.
        sessions: list of dicts with 'start_time' and 'end_time' (datetime objects)
        """
        self._sessions = sessions
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fill background
        painter.fillRect(self.rect(), self._bg_color)

        padding_left = 50
        padding_right = 20
        padding_top = 30
        padding_bottom = 40

        chart_w = self.width() - padding_left - padding_right
        chart_h = self.height() - padding_top - padding_bottom

        # Calculate cumulative data for each hour (0-24)
        hourly_minutes = [0] * 25  # 0 to 24 hours

        for session in self._sessions:
            start_time = session.get("start_time")
            end_time = session.get("end_time")
            if not start_time or not end_time:
                continue

            # For each hour, add minutes from sessions that ended by that hour
            for hour in range(25):
                hour_end = hour * 60  # minutes from start of day
                # Add duration of this session if it ended by this hour
                session_start_min = start_time.hour * 60 + start_time.minute
                session_end_min = end_time.hour * 60 + end_time.minute

                # Session contributes to this hour if it ended by this hour
                if session_end_min <= hour_end:
                    duration = session_end_min - session_start_min
                    if duration > 0:
                        hourly_minutes[hour] += duration

        # Max Y value (in minutes)
        max_minutes = max(hourly_minutes) if hourly_minutes else 60
        if max_minutes < 60:
            max_minutes = 60  # At least 1 hour scale
        # Round up to nice number
        max_minutes = ((max_minutes // 60) + 1) * 60

        # Draw grid lines and Y-axis labels
        painter.setPen(QPen(self._grid_color, 1))
        painter.setFont(QFont("Segoe UI", 9))

        num_y_gridlines = 4
        for i in range(num_y_gridlines + 1):
            y_ratio = i / num_y_gridlines
            y = padding_top + chart_h - y_ratio * chart_h

            # Grid line
            painter.drawLine(
                int(padding_left),
                int(y),
                int(self.width() - padding_right),
                int(y),
            )

            # Y-axis label (hours)
            minutes_val = int(y_ratio * max_minutes)
            hours_val = minutes_val // 60
            label = f"{hours_val}h"
            painter.setPen(QPen(self._text_color))
            painter.drawText(
                0,
                int(y - 8),
                padding_left - 10,
                16,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                label,
            )
            painter.setPen(QPen(self._grid_color, 1))

        # Draw X-axis labels (every 4 hours)
        painter.setPen(QPen(self._text_color))
        for hour in range(0, 25, 4):
            x_ratio = hour / 24
            x = padding_left + x_ratio * chart_w
            label = f"{hour:02d}"
            painter.drawText(
                int(x - 15),
                int(padding_top + chart_h + 5),
                30,
                20,
                Qt.AlignmentFlag.AlignCenter,
                label,
            )

        # Draw X-axis title
        painter.drawText(
            int(padding_left + chart_w / 2 - 30),
            int(self.height() - 5),
            60,
            20,
            Qt.AlignmentFlag.AlignCenter,
            "Hour",
        )

        if not self._sessions:
            # No data message
            painter.setPen(QPen(self._text_color))
            painter.setFont(QFont("Segoe UI", 14))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "No study sessions today",
            )
            painter.end()
            return

        # Draw step line
        line_pen = QPen(self._line_color, 3)
        line_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        line_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(line_pen)

        points = []
        for hour in range(25):
            x_ratio = hour / 24
            x = padding_left + x_ratio * chart_w
            y_ratio = hourly_minutes[hour] / max_minutes
            y = padding_top + chart_h - y_ratio * chart_h
            points.append(QPointF(x, y))

        # Draw step line (horizontal then vertical)
        if len(points) > 1:
            for i in range(len(points) - 1):
                # Horizontal line
                painter.drawLine(points[i], QPointF(points[i + 1].x(), points[i].y()))
                # Vertical step
                painter.drawLine(
                    QPointF(points[i + 1].x(), points[i].y()), points[i + 1]
                )

        # Draw area under the curve (optional, subtle fill)
        if len(points) > 1:
            fill_color = QColor(self._line_color)
            fill_color.setAlpha(30)

            # Create polygon for fill
            from PyQt6.QtGui import QPolygonF

            polygon = QPolygonF()
            polygon.append(QPointF(padding_left, padding_top + chart_h))
            for p in points:
                polygon.append(p)
            polygon.append(QPointF(points[-1].x(), padding_top + chart_h))

            painter.setBrush(fill_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(polygon)

        painter.end()
