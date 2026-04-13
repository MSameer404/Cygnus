# src/app/ui/widgets/snapshot_widget.py
"""Hidden widget purely for rendering the daily snapshot to an image."""

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
from app.core import todo_manager


class SnapshotWidget(QWidget):
    """Off-screen widget to render snapshot."""

    def __init__(self, target_date: date, total_seconds: int, parent=None):
        super().__init__(parent)
        self.target_date = target_date
        self.total_seconds = total_seconds
        
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
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(20)

        # ---------- Header: Date / Day ----------
        date_str = self.target_date.strftime("%B %d, %Y - %A")
        date_label = QLabel(date_str)
        date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #A6ACCD;")
        layout.addWidget(date_label)

        # ---------- Title: Total Time (HH:MM:SS) ----------
        hours = self.total_seconds // 3600
        minutes = (self.total_seconds % 3600) // 60
        seconds = self.total_seconds % 60
        hhmmss_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        time_label = QLabel(hhmmss_str)
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_label.setStyleSheet("font-size: 80px; font-weight: bold; color: #6C5CE7;")
        layout.addWidget(time_label)
        
        layout.addSpacing(20)

        # ---------- Body (Subjects left, Todos right) ----------
        body_layout = QHBoxLayout()
        body_layout.setSpacing(40)
        
        # Left: Subjects Breakdown
        left_frame = QFrame()
        left_frame.setProperty("class", "card")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(30, 30, 30, 30)
        
        sub_title = QLabel("Subject Breakdown")
        sub_title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        left_layout.addWidget(sub_title)
        
        breakdown = stats_engine.get_subject_breakdown(self.target_date, self.target_date)
        if not breakdown:
            empty_lbl = QLabel("No subjects tracked today.")
            empty_lbl.setStyleSheet("color: #7A819E; font-size: 16px;")
            left_layout.addWidget(empty_lbl)
        else:
            if isinstance(breakdown, dict):
                for name, item in breakdown.items():
                    row = QHBoxLayout()
                    
                    # Bulletproof dictionary access
                    c_hex = "#6C5CE7"
                    sec = 0
                    if isinstance(item, dict):
                        c_hex = item.get('color_hex', '#6C5CE7')
                        sec = item.get('seconds', 0)
                    elif isinstance(item, str):
                        # Graceful fallback if item somehow resolves to a string
                        c_hex = "#6C5CE7"
                        sec = 0
                    
                    color_dot = QLabel("●")
                    color_dot.setStyleSheet(f"color: {c_hex}; font-size: 20px;")
                    row.addWidget(color_dot)
                    
                    name_lbl = QLabel(str(name))
                    name_lbl.setStyleSheet("font-size: 18px;")
                    row.addWidget(name_lbl, stretch=1)
                    
                    val_lbl = QLabel(TimerEngine.format_seconds_short(int(sec)))
                    val_lbl.setStyleSheet("font-size: 18px; font-weight: bold;")
                    row.addWidget(val_lbl)
                    
                    left_layout.addLayout(row)
        left_layout.addStretch()
        body_layout.addWidget(left_frame, stretch=1)
        
        # Right: Todo List
        right_frame = QFrame()
        right_frame.setProperty("class", "card")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(30, 30, 30, 30)
        
        todo_title = QLabel("Today's To-Dos")
        todo_title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        right_layout.addWidget(todo_title)
        
        todos = todo_manager.list_todos(target_date=self.target_date)
        if not todos:
            empty_todo = QLabel("No todos scheduled for today.")
            empty_todo.setStyleSheet("color: #7A819E; font-size: 16px;")
            right_layout.addWidget(empty_todo)
        else:
            for t in todos:
                row = QHBoxLayout()
                # Bulletproof todo attributes
                is_comp = getattr(t, 'is_completed', False)
                title_text = str(getattr(t, 'title', "Unknown task"))
                
                check = "☑" if is_comp else "☐"
                chk_lbl = QLabel(check)
                chk_lbl.setStyleSheet(f"font-size: 24px; color: {'#00CEC9' if is_comp else '#7A819E'};")
                row.addWidget(chk_lbl)
                
                t_lbl = QLabel(title_text)
                t_style = "font-size: 18px; text-decoration: line-through; color: #7A819E;" if is_comp else "font-size: 18px;"
                t_lbl.setStyleSheet(t_style)
                row.addWidget(t_lbl, stretch=1)
                
                right_layout.addLayout(row)
        right_layout.addStretch()
        body_layout.addWidget(right_frame, stretch=1)

        layout.addLayout(body_layout)
        layout.addStretch()

        # ---------- Footer (Profile) ----------
        footer = QFrame()
        footer.setStyleSheet("background-color: transparent;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(12)  # Nice gap between image and text
        footer_layout.addStretch()
        
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
                    36, 36,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                pfp = QLabel()
                pfp.setPixmap(pfp_pixmap)
                # Ensure it sits perfectly vertically centered in the row
                footer_layout.addWidget(pfp, alignment=Qt.AlignmentFlag.AlignVCenter)
            
        profile = profile_manager.get_profile()
        name = profile.get("name") or "Cygnus"
        p_class = profile.get("class") or ""
        target_exam = profile.get("target_exam") or ""
        daily_goal = profile.get("daily_goal_hours") or ""
        start_date = profile.get("start_date") or ""
        
        parts = [name]
        if p_class:
            parts.append(f"Class: {p_class}")
        if target_exam:
            parts.append(f"Target: {target_exam}")
        if daily_goal:
            parts.append(f"Goal: {daily_goal}h")
        if start_date:
            try:
                sd = date.fromisoformat(start_date)
                days = (self.target_date - sd).days
                parts.append(f"Day {days}")
            except ValueError:
                parts.append(f"Started: {start_date}")
        
        profile_lbl_text = " • ".join(parts)
        
        profile_lbl = QLabel(profile_lbl_text)
        profile_lbl.setStyleSheet("font-size: 16px; color: #A6ACCD; font-weight: bold;")
        footer_layout.addWidget(profile_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        footer_layout.addStretch()
        layout.addWidget(footer, alignment=Qt.AlignmentFlag.AlignBottom)
    
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
