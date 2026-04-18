# src/app/ui/widgets/snapshot_widget.py
"""Hidden widget purely for rendering the daily snapshot to an image."""

import json
import random
from datetime import date
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage, QPainter
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.core import profile_manager
from app.core.timer_engine import TimerEngine
from app.core import stats_engine
from app.core import task_manager


def get_random_quote() -> dict:
    """Load and return a random quote from quotes.json."""
    quotes_path = Path(__file__).parent.parent.parent / "data" / "quotes.json"
    try:
        with open(quotes_path, "r", encoding="utf-8") as f:
            quotes = json.load(f)
        return random.choice(quotes) if quotes else {"text": "Stay focused and keep learning!", "author": "Cygnus"}
    except Exception:
        return {"text": "Stay focused and keep learning!", "author": "Cygnus"}


class SnapshotWidget(QWidget):
    """Off-screen widget to render snapshot."""

    def __init__(self, target_date: date, total_seconds: int, parent=None):
        super().__init__(parent)
        self.target_date = target_date
        self.total_seconds = total_seconds
        self.quote = get_random_quote()
        
        # Fixed resolution (laptop screen ratio 16:9, e.g., 1280x720)
        self.setFixedSize(1280, 720)
        self.setObjectName("SnapshotWidget")
        
        # We must load the stylesheet to ensure perfect styling
        theme_path = Path(__file__).parent.parent.parent / "assets" / "theme.qss"
        if theme_path.exists():
            self.setStyleSheet(theme_path.read_text(encoding="utf8"))
            
        self._setup_ui()

    def _setup_ui(self):
        # Using a main frame to apply background explicitly
        main_frame = QFrame(self)
        main_frame.setFixedSize(1280, 720)
        main_frame.setStyleSheet("background-color: #1E1E2E; color: white;")
        
        layout = QVBoxLayout(main_frame)
        layout.setContentsMargins(50, 30, 50, 30)
        layout.setSpacing(20)

        # ---------- TOP ROW: Profile Card (Left) + Date/Time Card (Right) ----------
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

        # RIGHT: Date & Total Time Card
        date_time_card = QFrame()
        date_time_card.setStyleSheet("background-color: #252535; border-radius: 12px;")
        date_time_layout = QVBoxLayout(date_time_card)
        date_time_layout.setContentsMargins(20, 15, 20, 15)
        date_time_layout.setSpacing(8)
        date_time_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Today's Date (Header 3 style)
        date_str = self.target_date.strftime("%B %d, %Y")
        date_lbl = QLabel(date_str)
        date_lbl.setStyleSheet("font-size: 18px; color: #8B8BA0;")
        date_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_time_layout.addWidget(date_lbl)

        # Total Time (Header 1 style - BIG)
        time_str = TimerEngine.format_seconds_short(self.total_seconds)
        time_lbl = QLabel(time_str)
        time_lbl.setStyleSheet("font-size: 48px; font-weight: bold; color: #6C5CE7;")
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_time_layout.addWidget(time_lbl)

        top_row.addWidget(date_time_card, stretch=1)
        layout.addLayout(top_row)

        # ---------- MIDDLE SECTION: Subjects (Left) + Tasks (Right) ----------
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

        breakdown = stats_engine.get_subject_breakdown(self.target_date, self.target_date)
        if not breakdown:
            empty_lbl = QLabel("No subjects tracked today.")
            empty_lbl.setStyleSheet("color: #7A819E; font-size: 14px;")
            subjects_layout.addWidget(empty_lbl)
        else:
            if isinstance(breakdown, dict):
                for name, item in breakdown.items():
                    row = QHBoxLayout()
                    row.setSpacing(10)
                    
                    # Bulletproof dictionary access
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

        # RIGHT: Today's Tasks
        tasks_card = QFrame()
        tasks_card.setStyleSheet("background-color: #252535; border-radius: 12px;")
        tasks_layout = QVBoxLayout(tasks_card)
        tasks_layout.setContentsMargins(20, 20, 20, 20)
        tasks_layout.setSpacing(12)

        task_title = QLabel("Today's Tasks")
        task_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #EAEAF0; margin-bottom: 5px;")
        tasks_layout.addWidget(task_title)

        # Due today, excluding dumped and items moved to the work table
        tasks = [
            t
            for t in task_manager.list_tasks(target_date=self.target_date)
            if not t.in_work
        ]
        if not tasks:
            empty_task = QLabel("No tasks scheduled for today.")
            empty_task.setStyleSheet("color: #7A819E; font-size: 14px;")
            tasks_layout.addWidget(empty_task)
        else:
            for t in tasks:
                row = QHBoxLayout()
                row.setSpacing(8)
                
                is_comp = getattr(t, 'is_completed', False)
                title_text = str(getattr(t, 'title', "Unknown task"))
                
                check = "☑" if is_comp else "☐"
                chk_lbl = QLabel(check)
                chk_lbl.setStyleSheet(f"font-size: 18px; color: {'#00CEC9' if is_comp else '#7A819E'};")
                row.addWidget(chk_lbl)
                
                t_lbl = QLabel(title_text)
                t_style = "font-size: 14px; text-decoration: line-through; color: #7A819E;" if is_comp else "font-size: 14px; color: #EAEAF0;"
                t_lbl.setStyleSheet(t_style)
                row.addWidget(t_lbl, stretch=1)
                
                tasks_layout.addLayout(row)
        tasks_layout.addStretch()
        middle_row.addWidget(tasks_card, stretch=1)

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
    
    def generate_image(self) -> QImage:
        """Render widget to a QImage."""
        self.ensurePolished()
        img = QImage(self.size(), QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.render(painter)
        painter.end()
        return img
