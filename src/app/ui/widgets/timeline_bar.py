# src/app/ui/widgets/timeline_bar.py
"""24-hour horizontal timeline bar showing study sessions as colored blocks."""

from datetime import date

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QPainterPath
from PyQt6.QtWidgets import QWidget, QToolTip

from app.core import session_manager, subject_manager
from app.core.timer_engine import TimerEngine


class TimelineBar(QWidget):
    """Paints a 24h bar with colored blocks for each study session."""

    def __init__(self, target_date: date | None = None, parent=None):
        super().__init__(parent)
        self._date = target_date or date.today()
        self._sessions = []
        self._subject_cache = {}
        self.setMinimumHeight(56)
        self.setMaximumHeight(56)
        self.setMouseTracking(True)
        self.refresh()

    def set_date(self, target_date: date):
        self._date = target_date
        self.refresh()

    def refresh(self):
        """Reload sessions for the current date."""
        self._sessions = session_manager.get_sessions_for_date(self._date)
        # Cache subject colors
        for s in self._sessions:
            if s.subject_id not in self._subject_cache:
                subj = subject_manager.get_subject(s.subject_id)
                self._subject_cache[s.subject_id] = subj
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width() - 16  # padding
        h = self.height()
        x_offset = 8
        bar_y = 20
        bar_h = h - 32

        # Background track
        track = QPainterPath()
        track.addRoundedRect(QRectF(x_offset, bar_y, w, bar_h), 6, 6)
        painter.fillPath(track, QColor("#252535"))

        # Hour markers
        painter.setPen(QPen(QColor("#3A3A50"), 1))
        font = QFont("Segoe UI", 8)
        painter.setFont(font)
        for hour in range(0, 25, 3):
            x = x_offset + (hour / 24) * w
            painter.drawLine(int(x), bar_y, int(x), bar_y + bar_h)
            if hour < 24:
                painter.setPen(QPen(QColor("#8B8BA0"), 1))
                painter.drawText(
                    QRectF(x - 12, bar_y + bar_h + 2, 24, 12),
                    Qt.AlignmentFlag.AlignCenter,
                    f"{hour:02d}",
                )
                painter.setPen(QPen(QColor("#3A3A50"), 1))

        # Session blocks
        for s in self._sessions:
            start_minutes = s.start_time.hour * 60 + s.start_time.minute
            end_minutes = s.end_time.hour * 60 + s.end_time.minute
            if end_minutes <= start_minutes:
                end_minutes = 24 * 60  # spans to midnight

            x1 = x_offset + (start_minutes / (24 * 60)) * w
            x2 = x_offset + (end_minutes / (24 * 60)) * w
            block_w = max(x2 - x1, 3)  # min 3px visible

            subj = self._subject_cache.get(s.subject_id)
            color = QColor(subj.color_hex if subj else "#6C5CE7")

            block = QPainterPath()
            block.addRoundedRect(QRectF(x1, bar_y + 2, block_w, bar_h - 4), 3, 3)
            painter.fillPath(block, color)

        painter.end()

    def mouseMoveEvent(self, event):
        """Show tooltip on hover over a session block."""
        pos = event.position() if hasattr(event, 'position') else event.pos()
        x = pos.x()
        w = self.width() - 16
        x_offset = 8

        for s in self._sessions:
            start_min = s.start_time.hour * 60 + s.start_time.minute
            end_min = s.end_time.hour * 60 + s.end_time.minute
            if end_min <= start_min:
                end_min = 24 * 60

            x1 = x_offset + (start_min / (24 * 60)) * w
            x2 = x_offset + (end_min / (24 * 60)) * w

            if x1 <= x <= x2:
                subj = self._subject_cache.get(s.subject_id)
                name = subj.name if subj else "Unknown"
                t1 = s.start_time.strftime("%H:%M")
                t2 = s.end_time.strftime("%H:%M")
                dur = TimerEngine.format_seconds_short(s.duration_seconds)
                QToolTip.showText(
                    event.globalPosition().toPoint(),
                    f"{name}\n{t1} – {t2} ({dur})",
                )
                return

        QToolTip.hideText()
