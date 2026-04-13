# src/app/ui/widgets/pie_chart.py
"""Custom-painted donut/pie chart for subject breakdown."""


from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QPainterPath
from PyQt6.QtWidgets import QWidget



class PieChart(QWidget):
    """Donut chart showing subject time breakdown."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: dict[str, dict] = {}  # {name: {seconds, color_hex}}
        self.setMinimumSize(220, 220)

    def set_data(self, data: dict[str, dict]):
        """Set chart data: {subject_name: {seconds: int, color_hex: str}}."""
        self._data = data
        self.update()

    def paintEvent(self, event):
        if not self._data:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor("#8B8BA0")))
            painter.setFont(QFont("Segoe UI", 12))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data")
            painter.end()
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = min(self.width(), self.height()) - 20
        cx = self.width() / 2
        cy = self.height() / 2
        outer_r = size / 2
        inner_r = outer_r * 0.6

        rect = QRectF(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2)
        inner_rect = QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)

        total = sum(d["seconds"] for d in self._data.values())
        if total == 0:
            return

        start_angle = 90 * 16  # Start from top

        for name, info in self._data.items():
            span = (info["seconds"] / total) * 360 * 16
            color = QColor(info["color_hex"])

            # Draw arc segment
            path = QPainterPath()
            path.arcMoveTo(rect, start_angle / 16)
            path.arcTo(rect, start_angle / 16, span / 16)
            path.arcTo(inner_rect, (start_angle + span) / 16, -span / 16)
            path.closeSubpath()

            painter.fillPath(path, color)

            # Draw thin separator
            painter.setPen(QPen(QColor("#0F0F14"), 2))
            painter.drawPath(path)

            start_angle += span

        # Center text
        painter.setPen(QPen(QColor("#EAEAF0")))
        painter.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        hours = total / 3600
        painter.drawText(
            QRectF(cx - inner_r, cy - 14, inner_r * 2, 28),
            Qt.AlignmentFlag.AlignCenter,
            f"{hours:.1f}h",
        )

        # Legend below
        legend_y = cy + outer_r + 16
        legend_x = 10
        painter.setFont(QFont("Segoe UI", 10))

        for name, info in self._data.items():
            if legend_y > self.height() - 10:
                break
            color = QColor(info["color_hex"])

            # Dot
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(legend_x), int(legend_y), 8, 8)

            # Label
            painter.setPen(QPen(QColor("#EAEAF0")))
            pct = (info["seconds"] / total * 100) if total > 0 else 0
            text = f"{name} ({pct:.0f}%)"
            painter.drawText(int(legend_x + 14), int(legend_y + 9), text)

            legend_x += painter.fontMetrics().horizontalAdvance(text) + 28
            if legend_x > self.width() - 60:
                legend_x = 10
                legend_y += 18

        painter.end()
