# src/app/ui/widgets/week_report_dialog.py
"""Week report dialog showing total time and daily bar chart."""

from datetime import date, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core import stats_engine
from app.core.timer_engine import TimerEngine
from app.ui.widgets.bar_chart import BarChart


class WeekReportDialog(QDialog):
    """Dialog displaying weekly study report with total time and daily breakdown."""

    def __init__(
        self,
        week_start: date,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.week_start = week_start
        self.week_end = week_start + timedelta(days=6)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Build the dialog UI."""
        self.setWindowTitle("Week Report")
        self.setMinimumSize(600, 500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header with week range
        header = QLabel(
            f"<h2>Week Report</h2>"
            f"<p style='color: #8B8BA0; font-size: 14px;'>"
            f"{self.week_start.strftime('%b %d')} – {self.week_end.strftime('%b %d, %Y')}"
            f"</p>"
        )
        header.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(header)

        # Total time section
        total_section = QWidget()
        total_section.setStyleSheet(
            "background-color: #6C5CE7; border-radius: 12px; padding: 20px;"
        )
        total_layout = QVBoxLayout(total_section)
        total_layout.setContentsMargins(0, 0, 0, 0)
        total_layout.setSpacing(8)

        total_label = QLabel("Total Study Time")
        total_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 14px;")
        total_layout.addWidget(total_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self._total_value = QLabel("0h 0m")
        self._total_value.setStyleSheet(
            "color: white; font-size: 36px; font-weight: bold;"
        )
        self._total_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        total_layout.addWidget(self._total_value)

        layout.addWidget(total_section)

        # Daily breakdown chart section
        chart_section = QWidget()
        chart_section.setStyleSheet(
            "background-color: #1A1A24; border-radius: 12px; border: 1px solid #3A3A50;"
        )
        chart_layout = QVBoxLayout(chart_section)
        chart_layout.setContentsMargins(16, 16, 16, 16)

        chart_title = QLabel("Daily Study Time")
        chart_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #EAEAF0;")
        chart_layout.addWidget(chart_title)

        # Bar chart
        self._bar_chart = BarChart()
        self._bar_chart.setMinimumHeight(250)
        chart_layout.addWidget(self._bar_chart)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(24)

        # Best day
        best_container = QWidget()
        best_layout = QVBoxLayout(best_container)
        best_layout.setContentsMargins(0, 0, 0, 0)
        best_layout.setSpacing(4)

        best_title = QLabel("Best Day")
        best_title.setStyleSheet("color: #8B8BA0; font-size: 12px;")
        best_layout.addWidget(best_title)

        self._best_day = QLabel("—")
        self._best_day.setStyleSheet("color: #1D9E75; font-size: 16px; font-weight: bold;")
        best_layout.addWidget(self._best_day)

        stats_row.addWidget(best_container)

        # Daily average
        avg_container = QWidget()
        avg_layout = QVBoxLayout(avg_container)
        avg_layout.setContentsMargins(0, 0, 0, 0)
        avg_layout.setSpacing(4)

        avg_title = QLabel("Daily Average")
        avg_title.setStyleSheet("color: #8B8BA0; font-size: 12px;")
        avg_layout.addWidget(avg_title)

        self._daily_avg = QLabel("0h 0m")
        self._daily_avg.setStyleSheet("color: #00CEC9; font-size: 16px; font-weight: bold;")
        avg_layout.addWidget(self._daily_avg)

        stats_row.addWidget(avg_container)

        # Study days count
        days_container = QWidget()
        days_layout = QVBoxLayout(days_container)
        days_layout.setContentsMargins(0, 0, 0, 0)
        days_layout.setSpacing(4)

        days_title = QLabel("Study Days")
        days_title.setStyleSheet("color: #8B8BA0; font-size: 12px;")
        days_layout.addWidget(days_title)

        self._study_days = QLabel("0/7")
        self._study_days.setStyleSheet("color: #FDCB6E; font-size: 16px; font-weight: bold;")
        days_layout.addWidget(self._study_days)

        stats_row.addWidget(days_container)
        stats_row.addStretch()

        chart_layout.addLayout(stats_row)
        layout.addWidget(chart_section)

        layout.addStretch()

        # Close button
        button_row = QHBoxLayout()
        button_row.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setProperty("class", "secondary")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        button_row.addWidget(close_btn)

        layout.addLayout(button_row)

    def _load_data(self):
        """Load and display weekly data."""
        # Get daily totals
        daily_totals = stats_engine.get_weekly_totals(self.week_start)
        bar_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        # Calculate total
        total_seconds = sum(daily_totals)
        self._total_value.setText(TimerEngine.format_seconds_short(total_seconds))

        # Set bar chart data
        self._bar_chart.set_data(daily_totals, bar_labels, accent="#6C5CE7")

        # Calculate best day
        if any(daily_totals):
            max_idx = daily_totals.index(max(daily_totals))
            best_day_name = bar_labels[max_idx]
            best_day_seconds = daily_totals[max_idx]
            self._best_day.setText(
                f"{best_day_name} ({TimerEngine.format_seconds_short(best_day_seconds)})"
            )
        else:
            self._best_day.setText("—")

        # Calculate daily average (only counting days with study time)
        study_days = sum(1 for t in daily_totals if t > 0)
        self._study_days.setText(f"{study_days}/7")

        if study_days > 0:
            avg_seconds = total_seconds // study_days
            self._daily_avg.setText(TimerEngine.format_seconds_short(avg_seconds))
        else:
            self._daily_avg.setText("0h 0m")
