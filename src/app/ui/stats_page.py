"""Statistics & analytics page with charts and summary cards."""

import calendar
import traceback
from datetime import date, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabBar,
    QVBoxLayout,
    QWidget,
)

from app.core import stats_engine
from app.core.timer_engine import TimerEngine
from app.ui.widgets.bar_chart import BarChart
from app.ui.widgets.heatmap import HeatmapWidget
from app.ui.widgets.pie_chart import PieChart
from app.ui.widgets.snapshot_widget import SnapshotWidget


class StatsPage(QWidget):
    """Full analytics page with tab views: Day, Week, Month, Year."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_date = date.today()
        self._current_tab = 0  # 0=Day, 1=Week, 2=Month, 3=Year
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        self._layout = QVBoxLayout(content)
        self._layout.setContentsMargins(40, 30, 40, 30)
        self._layout.setSpacing(20)

        # ---------- Header ----------
        header = QHBoxLayout()
        title = QLabel("Statistics")
        title.setProperty("class", "heading")
        header.addWidget(title)
        header.addStretch()
        self._layout.addLayout(header)

        # ---------- Tab Bar ----------
        self._tab_bar = QTabBar()
        self._tab_bar.addTab("Day")
        self._tab_bar.addTab("Week")
        self._tab_bar.addTab("Month")
        self._tab_bar.addTab("Year")
        self._tab_bar.currentChanged.connect(self._on_tab_changed)
        self._layout.addWidget(self._tab_bar)

        # ---------- Date Navigation ----------
        nav_row = QHBoxLayout()

        self._prev_btn = QPushButton("Prev")
        self._prev_btn.setProperty("class", "ghost")
        self._prev_btn.setFixedHeight(36)
        self._prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._prev_btn.clicked.connect(self._go_prev)
        nav_row.addWidget(self._prev_btn)

        self._download_btn = QPushButton("Report")
        self._download_btn.setProperty("class", "secondary")
        self._download_btn.setFixedHeight(36)
        self._download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._download_btn.clicked.connect(self._download_snapshot)
        nav_row.addWidget(self._download_btn)

        self._date_label = QLabel()
        self._date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._date_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        nav_row.addWidget(self._date_label, stretch=1)

        self._today_btn = QPushButton("Today")
        self._today_btn.setProperty("class", "secondary")
        self._today_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._today_btn.clicked.connect(self._go_today)
        nav_row.addWidget(self._today_btn)

        self._next_btn = QPushButton("Next")
        self._next_btn.setProperty("class", "ghost")
        self._next_btn.setFixedHeight(36)
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.clicked.connect(self._go_next)
        nav_row.addWidget(self._next_btn)

        self._layout.addLayout(nav_row)

        # ---------- Summary Cards ----------
        self._cards_layout = QHBoxLayout()
        self._cards_layout.setSpacing(16)

        self._total_card = self._make_card("Total Time", "0h", "#6C5CE7")
        self._avg_card = self._make_card("Daily Average", "0h", "#00CEC9")
        self._streak_card = self._make_card("Streak", "0 days", "#FDCB6E")
        self._best_card = self._make_card("Best Day", "0h", "#FF6B6B")

        self._cards_layout.addWidget(self._total_card)
        self._cards_layout.addWidget(self._avg_card)
        self._cards_layout.addWidget(self._streak_card)
        self._cards_layout.addWidget(self._best_card)
        self._layout.addLayout(self._cards_layout)

        # ---------- Charts Row ----------
        charts_row = QHBoxLayout()
        charts_row.setSpacing(20)

        # Pie chart
        pie_frame = QFrame()
        pie_frame.setProperty("class", "card")
        pie_layout = QVBoxLayout(pie_frame)
        pie_title = QLabel("Subject Breakdown")
        pie_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        pie_layout.addWidget(pie_title)
        self._pie_chart = PieChart()
        self._pie_chart.setMinimumSize(250, 280)
        pie_layout.addWidget(self._pie_chart)
        charts_row.addWidget(pie_frame)

        # Bar chart
        bar_frame = QFrame()
        bar_frame.setProperty("class", "card")
        bar_layout = QVBoxLayout(bar_frame)
        self._bar_title = QLabel("Daily Breakdown")
        self._bar_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        bar_layout.addWidget(self._bar_title)
        self._bar_chart = BarChart()
        self._bar_chart.setMinimumHeight(250)
        bar_layout.addWidget(self._bar_chart)
        charts_row.addWidget(bar_frame, stretch=1)

        self._layout.addLayout(charts_row)

        # ---------- Heatmap ----------
        heatmap_frame = QFrame()
        heatmap_frame.setProperty("class", "card")
        heatmap_layout = QVBoxLayout(heatmap_frame)
        heatmap_title = QLabel("Study Heatmap")
        heatmap_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        heatmap_layout.addWidget(heatmap_title)
        self._heatmap = HeatmapWidget()
        self._heatmap.setMinimumHeight(140)
        heatmap_layout.addWidget(self._heatmap)
        self._layout.addWidget(heatmap_frame)

        self._layout.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _make_card(self, title: str, value: str, accent: str) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)

        val = QLabel(value)
        val.setObjectName(f"stat_{title.replace(' ', '_').lower()}")
        val.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {accent};")
        layout.addWidget(val)

        lbl = QLabel(title)
        lbl.setProperty("class", "caption")
        layout.addWidget(lbl)

        return card

    def _update_card_value(self, card: QFrame, value: str):
        for child in card.findChildren(QLabel):
            if child.objectName().startswith("stat_"):
                child.setText(value)
                break

    def _on_tab_changed(self, index: int):
        self._current_tab = index
        self._current_date = date.today()
        self._refresh()

    def _go_prev(self):
        if self._current_tab == 0:  # Day
            self._current_date -= timedelta(days=1)
        elif self._current_tab == 1:  # Week
            self._current_date -= timedelta(weeks=1)
        elif self._current_tab == 2:  # Month
            m = self._current_date.month - 1
            y = self._current_date.year
            if m < 1:
                m = 12
                y -= 1
            self._current_date = date(y, m, 1)
        elif self._current_tab == 3:  # Year
            self._current_date = date(self._current_date.year - 1, 1, 1)
        self._refresh()

    def _go_next(self):
        if self._current_tab == 0:
            self._current_date += timedelta(days=1)
        elif self._current_tab == 1:
            self._current_date += timedelta(weeks=1)
        elif self._current_tab == 2:
            m = self._current_date.month + 1
            y = self._current_date.year
            if m > 12:
                m = 1
                y += 1
            self._current_date = date(y, m, 1)
        elif self._current_tab == 3:
            self._current_date = date(self._current_date.year + 1, 1, 1)
        self._refresh()

    def _go_today(self):
        self._current_date = date.today()
        self._refresh()

    def _refresh(self):
        """Refresh all stats for the current tab and date."""
        tab = self._current_tab
        d = self._current_date

        if tab == 0:  # Day
            self._download_btn.show()
            self._date_label.setText(d.strftime("%A, %B %d, %Y"))
            start, end = d, d
            bar_values = [stats_engine.get_daily_total(d)]
            bar_labels = [d.strftime("%a")]
            self._bar_title.setText("Today's Total")

        elif tab == 1:  # Week
            self._download_btn.hide()
            start = stats_engine.get_week_start(d)
            end = start + timedelta(days=6)
            self._date_label.setText(f"{start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}")
            bar_values = stats_engine.get_weekly_totals(start)
            bar_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            self._bar_title.setText("Daily Breakdown")

        elif tab == 2:  # Month
            self._download_btn.hide()
            start = date(d.year, d.month, 1)
            num_days = calendar.monthrange(d.year, d.month)[1]
            end = date(d.year, d.month, num_days)
            self._date_label.setText(d.strftime("%B %Y"))
            bar_values = stats_engine.get_monthly_totals(d.year, d.month)
            bar_labels = [str(i + 1) if (i + 1) % 5 == 0 or i == 0 else "" for i in range(num_days)]
            self._bar_title.setText("Daily Breakdown")

        else:  # Year
            self._download_btn.hide()
            start = date(d.year, 1, 1)
            end = date(d.year, 12, 31)
            self._date_label.setText(str(d.year))
            # Monthly totals for year view
            bar_values = []
            bar_labels = []
            for m in range(1, 13):
                month_start = date(d.year, m, 1)
                month_end = date(d.year, m, calendar.monthrange(d.year, m)[1])
                bar_values.append(stats_engine.get_total_for_range(month_start, month_end))
                bar_labels.append(calendar.month_abbr[m])
            self._bar_title.setText("Monthly Breakdown")

        # Summary cards
        total = stats_engine.get_total_for_range(start, end)
        avg = stats_engine.get_average_daily(start, end)
        streak = stats_engine.get_streak()
        best_date, best_secs = stats_engine.get_best_day(start, end)

        self._update_card_value(self._total_card, TimerEngine.format_seconds_short(total))
        self._update_card_value(self._avg_card, TimerEngine.format_seconds_short(avg))
        self._update_card_value(self._streak_card, f"{streak} days")
        self._update_card_value(
            self._best_card,
            f"{TimerEngine.format_seconds_short(best_secs)}" if best_secs > 0 else "—",
        )

        # Charts
        breakdown = stats_engine.get_subject_breakdown(start, end)
        self._pie_chart.set_data(breakdown)
        self._bar_chart.set_data(bar_values, bar_labels)

        # Heatmap (always year view)
        year = d.year
        heatmap_data = stats_engine.get_heatmap_data(year)
        self._heatmap.set_data(heatmap_data, year)

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh()

    def _download_snapshot(self):
        """Generate and save the image snapshot of the current day."""
        if self._current_tab != 0:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Snapshot",
            f"Cygnus_Snapshot_{self._current_date.strftime('%Y-%m-%d')}.png",
            "Images (*.png)"
        )
        
        if not file_path:
            return
            
        try:
            total_time = stats_engine.get_daily_total(self._current_date)
            snapsht_widget = SnapshotWidget(self._current_date, total_time)
            
            # Get the image
            image = snapsht_widget.generate_image()
            
            if image.save(file_path):
                QMessageBox.information(self, "Success", f"Snapshot saved successfully to:\n{file_path}")
            else:
                QMessageBox.warning(self, "Error", "Failed to save the snapshot image.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while generating snapshot:\n{traceback.format_exc()}")
