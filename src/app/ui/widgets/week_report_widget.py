# src/app/ui/widgets/week_report_widget.py
"""Hidden widget purely for rendering the weekly report to an image."""

import json
import random
from datetime import date, timedelta
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.core import profile_manager
from app.core import stats_engine
from app.core.timer_engine import TimerEngine
from app.ui.widgets.bar_chart import BarChart


def get_random_quote() -> dict:
    """Load and return a random quote from quotes.json."""
    quotes_path = Path(__file__).parent.parent.parent / "data" / "quotes.json"
    try:
        with open(quotes_path, "r", encoding="utf-8") as f:
            quotes = json.load(f)
        return random.choice(quotes) if quotes else {"text": "Stay focused and keep learning!", "author": "Cygnus"}
    except Exception:
        return {"text": "Stay focused and keep learning!", "author": "Cygnus"}


class WeekReportWidget(QWidget):
    """Off-screen widget to render week report snapshot."""

    def __init__(self, week_start: date, parent=None):
        super().__init__(parent)
        self.week_start = week_start
        self.week_end = week_start + timedelta(days=6)
        self.quote = get_random_quote()
        
        # Fixed resolution (laptop screen ratio 16:9, e.g., 1280x720)
        self.setFixedSize(1280, 720)
        self.setObjectName("WeekReportWidget")
        
        # Load the stylesheet to ensure perfect styling
        theme_path = Path(__file__).parent.parent.parent / "assets" / "theme.qss"
        if theme_path.exists():
            self.setStyleSheet(theme_path.read_text(encoding="utf8"))
            
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Build the week report UI."""
        # Using a main frame to apply background explicitly
        main_frame = QFrame(self)
        main_frame.setFixedSize(1280, 720)
        main_frame.setStyleSheet("background-color: #1E1E2E; color: white;")
        
        layout = QVBoxLayout(main_frame)
        layout.setContentsMargins(50, 30, 50, 30)
        layout.setSpacing(20)

        # ---------- TOP ROW: Profile Card (Left) + Week Date/Total Time Card (Right) ----------
        top_row = QHBoxLayout()
        top_row.setSpacing(20)

        # LEFT: Profile Card
        profile_card = QFrame()
        profile_card.setStyleSheet("background-color: #252535; border-radius: 12px;")
        profile_layout = QHBoxLayout(profile_card)
        profile_layout.setContentsMargins(20, 15, 20, 15)
        profile_layout.setSpacing(15)

        # Profile Picture
        pfp_path = profile_manager.get_profile_picture_path()
        if pfp_path:
            pfp_pixmap = QPixmap(str(pfp_path))
            if not pfp_pixmap.isNull():
                w, h = pfp_pixmap.width(), pfp_pixmap.height()
                if w != h:
                    side = min(w, h)
                    x = (w - side) // 2
                    y = (h - side) // 2
                    pfp_pixmap = pfp_pixmap.copy(x, y, side, side)
                pfp_pixmap = pfp_pixmap.scaled(
                    48, 48,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                pfp = QLabel()
                pfp.setPixmap(pfp_pixmap)
                profile_layout.addWidget(pfp, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Profile Details
        profile = profile_manager.get_profile()
        name = profile.get("name") or "Cygnus"
        p_class = profile.get("class") or ""
        target_exam = profile.get("target_exam") or ""
        
        profile_info = QVBoxLayout()
        profile_info.setSpacing(4)
        
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #EAEAF0;")
        profile_info.addWidget(name_lbl)
        
        details = []
        if p_class:
            details.append(f"Class {p_class}")
        if target_exam:
            details.append(target_exam)
        
        if details:
            details_lbl = QLabel(" • ".join(details))
            details_lbl.setStyleSheet("font-size: 14px; color: #8B8BA0;")
            profile_info.addWidget(details_lbl)
        
        profile_layout.addLayout(profile_info)
        profile_layout.addStretch()
        top_row.addWidget(profile_card, stretch=1)

        # RIGHT: Week Date & Total Time Card
        week_card = QFrame()
        week_card.setStyleSheet("background-color: #252535; border-radius: 12px;")
        week_layout = QVBoxLayout(week_card)
        week_layout.setContentsMargins(20, 15, 20, 15)
        week_layout.setSpacing(8)
        week_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Week Date Range (Header 3 style)
        week_str = f"{self.week_start.strftime('%b %d')} – {self.week_end.strftime('%b %d, %Y')}"
        week_lbl = QLabel(week_str)
        week_lbl.setStyleSheet("font-size: 18px; color: #8B8BA0;")
        week_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        week_layout.addWidget(week_lbl)

        # Total Weekly Time (Header 1 style - BIG)
        self._total_label = QLabel("0h 0m")
        self._total_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #6C5CE7;")
        self._total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        week_layout.addWidget(self._total_label)

        top_row.addWidget(week_card, stretch=1)
        layout.addLayout(top_row)

        # ---------- MIDDLE SECTION: Subject Breakdown (Left) + Daily Chart (Right) ----------
        middle_row = QHBoxLayout()
        middle_row.setSpacing(20)

        # LEFT: Subject Breakdown
        subjects_card = QFrame()
        subjects_card.setStyleSheet("background-color: #252535; border-radius: 12px;")
        subjects_layout = QVBoxLayout(subjects_card)
        subjects_layout.setContentsMargins(20, 20, 20, 20)
        subjects_layout.setSpacing(12)

        sub_title = QLabel("Subject Breakdown")
        sub_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #EAEAF0; margin-bottom: 5px;")
        subjects_layout.addWidget(sub_title)

        # Get weekly subject breakdown
        breakdown = stats_engine.get_subject_breakdown(self.week_start, self.week_end)
        if not breakdown:
            empty_lbl = QLabel("No subjects tracked this week.")
            empty_lbl.setStyleSheet("color: #7A819E; font-size: 14px;")
            subjects_layout.addWidget(empty_lbl)
        else:
            if isinstance(breakdown, dict):
                for name, item in breakdown.items():
                    row = QHBoxLayout()
                    row.setSpacing(10)
                    
                    c_hex = "#6C5CE7"
                    sec = 0
                    if isinstance(item, dict):
                        c_hex = item.get('color_hex', '#6C5CE7')
                        sec = item.get('seconds', 0)
                    elif isinstance(item, str):
                        c_hex = "#6C5CE7"
                        sec = 0
                    
                    color_dot = QLabel("●")
                    color_dot.setStyleSheet(f"color: {c_hex}; font-size: 16px;")
                    row.addWidget(color_dot)
                    
                    name_lbl = QLabel(str(name))
                    name_lbl.setStyleSheet("font-size: 15px; color: #EAEAF0;")
                    row.addWidget(name_lbl, stretch=1)
                    
                    # Subject time - slightly bigger
                    val_lbl = QLabel(TimerEngine.format_seconds_short(int(sec)))
                    val_lbl.setStyleSheet("font-size: 17px; font-weight: bold; color: #A29BFE;")
                    row.addWidget(val_lbl)
                    
                    subjects_layout.addLayout(row)
        subjects_layout.addStretch()
        middle_row.addWidget(subjects_card, stretch=1)

        # RIGHT: Daily Study Time Bar Chart
        chart_card = QFrame()
        chart_card.setStyleSheet("background-color: #252535; border-radius: 12px;")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(20, 20, 20, 20)
        chart_layout.setSpacing(12)

        chart_title = QLabel("Daily Study Time")
        chart_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #EAEAF0; margin-bottom: 5px;")
        chart_layout.addWidget(chart_title)

        self._bar_chart = BarChart()
        self._bar_chart.setMinimumHeight(180)
        chart_layout.addWidget(self._bar_chart)
        
        middle_row.addWidget(chart_card, stretch=1)
        layout.addLayout(middle_row, stretch=1)

        # ---------- BOTTOM: Random Quote ----------
        quote_card = QFrame()
        quote_card.setStyleSheet("background-color: #1A1A24; border-left: 3px solid #6C5CE7; border-radius: 8px;")
        quote_layout = QVBoxLayout(quote_card)
        quote_layout.setContentsMargins(15, 12, 15, 12)

        quote_text = QLabel(f'"{self.quote.get("text", "")}"')
        quote_text.setStyleSheet("font-size: 14px; color: #A6ACCD; font-style: italic;")
        quote_text.setWordWrap(True)
        quote_layout.addWidget(quote_text)

        quote_author = QLabel(f'— {self.quote.get("author", "Unknown")}')
        quote_author.setStyleSheet("font-size: 12px; color: #6B6B7B; margin-top: 4px;")
        quote_author.setAlignment(Qt.AlignmentFlag.AlignRight)
        quote_layout.addWidget(quote_author)

        layout.addWidget(quote_card)

        # ---------- FOOTER: Made by Cygnus ----------
        footer = QHBoxLayout()
        footer.addStretch()
        
        cygnus_mark = QLabel("Made by Cygnus")
        cygnus_mark.setStyleSheet("font-size: 12px; color: #6B6B7B;")
        footer.addWidget(cygnus_mark)
        
        layout.addLayout(footer)

    def _load_data(self):
        """Load and display weekly data."""
        # Get daily totals
        daily_totals = stats_engine.get_weekly_totals(self.week_start)
        bar_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        # Calculate total
        total_seconds = sum(daily_totals)
        self._total_label.setText(TimerEngine.format_seconds_short(total_seconds))

        # Set bar chart data
        self._bar_chart.set_data(daily_totals, bar_labels, accent="#6C5CE7")

    def generate_image(self) -> QImage:
        """Render this widget to a QImage."""
        self.ensurePolished()
        
        image = QImage(self.size(), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.render(painter)
        painter.end()
        
        return image
