# src/app/ui/task_page.py
"""Task page: Responsive Side-by-Side Monthly Calendar Navigation & Task List View."""

from datetime import date, timedelta
import calendar

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPainter, QFont, QLinearGradient
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QScrollArea,
    QFrame,
    QCheckBox,
    QComboBox,
)

from app.core import task_manager, subject_manager
from app.core.events import app_events


def hex_to_rgba(hex_str: str, alpha: float) -> str:
    """Helper to convert hex strings safely to rgba format for premium transparent QSS badges."""
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c*2 for c in hex_str])
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


class DayButton(QPushButton):
    """Custom circular/rounded calendar day button with hover state and task dot indicator."""

    def __init__(self, target_date: date, is_current_month: bool, has_tasks: bool, is_selected: bool, parent=None):
        super().__init__(parent)
        self._date = target_date
        self._is_current_month = is_current_month
        self._has_tasks = has_tasks
        self._is_selected = is_selected
        self.setFixedSize(38, 38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        is_hovered = self.underMouse()
        is_pressed = self.isDown()
        is_today = (self._date == date.today())

        # Circle backgrounds
        if self._is_selected:
            # Solid premium gradient circle
            gradient = QLinearGradient(0, 0, rect.width(), rect.height())
            gradient.setColorAt(0.0, QColor("#7F71EF"))
            gradient.setColorAt(1.0, QColor("#CBAACD"))
            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8, 8)
        elif is_today:
            # Glowing rose rounded outline for today
            painter.setBrush(QColor("rgba(255, 117, 143, 0.15)"))
            painter.setPen(QColor("#FF758F"))
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8, 8)
        elif is_pressed:
            painter.setBrush(QColor("rgba(255, 255, 255, 0.15)"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8, 8)
        elif is_hovered:
            painter.setBrush(QColor("rgba(255, 255, 255, 0.08)"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8, 8)
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(Qt.PenStyle.NoPen)

        # Font styles & text colors
        if self._is_selected:
            text_color = QColor("#FFFFFF")
        elif is_today:
            text_color = QColor("#FF758F")
        elif self._is_current_month:
            text_color = QColor("#ECFDF5")
        else:
            text_color = QColor("rgba(203, 170, 205, 0.35)")  # Faded out adjacent month

        painter.setPen(text_color)
        font = QFont("Segoe UI", 9)
        if self._is_selected or is_today:
            font.setBold(True)
        painter.setFont(font)

        # Draw day number text
        painter.drawText(rect.adjusted(0, 0, 0, -3), Qt.AlignmentFlag.AlignCenter, str(self._date.day))

        # Emerald task indicator dot
        if self._has_tasks:
            dot_color = QColor("#10B981") if not self._is_selected else QColor("#FFFFFF")
            painter.setBrush(dot_color)
            painter.setPen(Qt.PenStyle.NoPen)
            dot_size = 3
            painter.drawEllipse(
                int(rect.width() / 2 - dot_size / 2),
                int(rect.height() - 7),
                dot_size,
                dot_size
            )

        painter.end()


class TaskPage(QWidget):
    """Redesigned Task Tracker: side-by-side layout with daily tasks on left and navigation calendar on right."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._year = date.today().year
        self._month = date.today().month
        self._selected_date = date.today()

        self._setup_ui()
        app_events.data_reset.connect(self._on_data_reset)

    def _on_data_reset(self):
        self._year = date.today().year
        self._month = date.today().month
        self._selected_date = date.today()
        self._refresh()

    def _setup_ui(self):
        self.setObjectName("taskDashboard")
        self.setMinimumSize(950, 600)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---------- Header Bar ----------
        header = QWidget()
        header.setObjectName("pageHeader")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        title = QLabel("Task Planner")
        title.setProperty("class", "heading")
        header_layout.addWidget(title)
        header_layout.addStretch()
        main_layout.addWidget(header)

        # Separator Line
        separator = QFrame()
        separator.setObjectName("headerSeparator")
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)

        # ---------- Content Row (Side-by-Side) ----------
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(40, 24, 40, 30)
        content_layout.setSpacing(20)

        # 1. Left Panel: Daily Tasks
        self._task_card = QFrame()
        self._task_card.setProperty("class", "card")
        self._task_card.setMinimumWidth(440)
        
        task_layout = QVBoxLayout(self._task_card)
        task_layout.setContentsMargins(24, 24, 24, 24)
        task_layout.setSpacing(16)

        self._day_title = QLabel()
        self._day_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFD6E0;")
        task_layout.addWidget(self._day_title)

        # Task list scrollable frame
        self._task_scroll = QScrollArea()
        self._task_scroll.setWidgetResizable(True)
        self._task_scroll.setStyleSheet("background: transparent; border: none;")
        self._task_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self._task_inner = QWidget()
        self._task_inner_layout = QVBoxLayout(self._task_inner)
        self._task_inner_layout.setContentsMargins(0, 0, 0, 0)
        self._task_inner_layout.setSpacing(8)
        self._task_inner_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self._task_scroll.setWidget(self._task_inner)
        task_layout.addWidget(self._task_scroll, stretch=1)

        # Premium Quick-Add Panels
        add_panel = QVBoxLayout()
        add_panel.setSpacing(8)

        # Task title input
        self._task_input = QLineEdit()
        self._task_input.setPlaceholderText("Write a task and hit Enter...")
        self._task_input.setFixedHeight(38)
        self._task_input.setStyleSheet("""
            QLineEdit {
                background: rgba(40, 15, 45, 0.45);
                border: 1px solid rgba(203, 170, 205, 0.15);
                border-radius: 8px;
                padding: 0px 12px;
                color: #ECFDF5;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #7F71EF;
            }
        """)
        self._task_input.returnPressed.connect(self._create_quick_task)
        add_panel.addWidget(self._task_input)

        # Dropdowns Selector row
        selectors_row = QHBoxLayout()
        selectors_row.setSpacing(8)

        # Subject Combo Box
        self._subject_combo = QComboBox()
        self._subject_combo.setFixedHeight(36)
        self._subject_combo.setStyleSheet("""
            QComboBox {
                background: rgba(40, 15, 45, 0.45);
                border: 1px solid rgba(203, 170, 205, 0.15);
                border-radius: 6px;
                padding: 0px 10px;
                color: #ECFDF5;
                font-size: 12px;
            }
            QComboBox::drop-down { border: none; }
        """)
        selectors_row.addWidget(self._subject_combo, stretch=1)

        # Priority Combo Box
        self._priority_combo = QComboBox()
        self._priority_combo.setFixedHeight(36)
        self._priority_combo.setStyleSheet("""
            QComboBox {
                background: rgba(40, 15, 45, 0.45);
                border: 1px solid rgba(203, 170, 205, 0.15);
                border-radius: 6px;
                padding: 0px 10px;
                color: #ECFDF5;
                font-size: 12px;
            }
            QComboBox::drop-down { border: none; }
        """)
        self._priority_combo.addItem("🟢  Low Priority", "low")
        self._priority_combo.addItem("🟡  Medium Priority", "med")
        self._priority_combo.addItem("🔴  High Priority", "high")
        self._priority_combo.setCurrentIndex(1)  # Default to Medium
        selectors_row.addWidget(self._priority_combo, stretch=1)

        # Add button
        add_btn = QPushButton("+ Add")
        add_btn.setProperty("class", "task-create-btn")
        add_btn.setFixedHeight(36)
        add_btn.setFixedWidth(74)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._create_quick_task)
        selectors_row.addWidget(add_btn)

        add_panel.addLayout(selectors_row)
        task_layout.addLayout(add_panel)
        content_layout.addWidget(self._task_card, stretch=5)

        # Right Column Stack (Snug Calendar + Motivational Tip Card below)
        right_column = QVBoxLayout()
        right_column.setSpacing(16)
        right_column.setContentsMargins(0, 0, 0, 0)

        # 2. Right Column Top: Snug Calendar Card
        self._calendar_card = QFrame()
        self._calendar_card.setProperty("class", "card")
        self._calendar_card.setFixedSize(420, 360)

        cal_layout = QVBoxLayout(self._calendar_card)
        cal_layout.setContentsMargins(18, 16, 18, 16)
        cal_layout.setSpacing(12)

        # Navigator Row (Prev Month, Label, Next Month)
        nav_row = QHBoxLayout()
        self._month_label = QLabel()
        self._month_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFD6E0;")

        prev_btn = QPushButton("◀")
        prev_btn.setFixedSize(30, 30)
        prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        prev_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                color: #CBAACD;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(127, 113, 239, 0.4);
                color: #FFF;
            }
        """)
        prev_btn.clicked.connect(self._go_prev_month)

        next_btn = QPushButton("▶")
        next_btn.setFixedSize(30, 30)
        next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        next_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                color: #CBAACD;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(127, 113, 239, 0.4);
                color: #FFF;
            }
        """)
        next_btn.clicked.connect(self._go_next_month)

        nav_row.addWidget(prev_btn)
        nav_row.addWidget(self._month_label, stretch=1, alignment=Qt.AlignmentFlag.AlignCenter)
        nav_row.addWidget(next_btn)
        cal_layout.addLayout(nav_row)

        # Weekdays header row
        week_grid = QGridLayout()
        week_grid.setSpacing(4)
        days_of_week = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        for col, day_name in enumerate(days_of_week):
            lbl = QLabel(day_name)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size: 10px; font-weight: bold; color: rgba(203, 170, 205, 0.45);")
            week_grid.addWidget(lbl, 0, col)

        cal_layout.addLayout(week_grid)

        # Dates Grid
        self._dates_grid = QGridLayout()
        self._dates_grid.setSpacing(4)
        cal_layout.addLayout(self._dates_grid, stretch=1)
        right_column.addWidget(self._calendar_card)

        # 3. Right Column Bottom: Motivational Insights Card (Utilizes remaining space elegantly!)
        self._extra_card = QFrame()
        self._extra_card.setProperty("class", "card")
        self._extra_card.setFixedWidth(420)

        extra_layout = QVBoxLayout(self._extra_card)
        extra_layout.setContentsMargins(20, 20, 20, 20)
        extra_layout.setSpacing(10)

        extra_title = QLabel("💡  Planner Insights")
        extra_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFD6E0;")
        extra_layout.addWidget(extra_title)

        extra_desc = QLabel(
            "“Focus on being productive instead of busy.”\n\n"
            "Use this calendar to plan your study sessions ahead of time. Active days with scheduled tasks are automatically highlighted with green indicator dots."
        )
        extra_desc.setWordWrap(True)
        extra_desc.setStyleSheet("color: rgba(203, 170, 205, 0.6); font-size: 12px; line-height: 1.6; font-style: italic;")
        extra_layout.addWidget(extra_desc)
        extra_layout.addStretch()

        right_column.addWidget(self._extra_card, stretch=1)
        content_layout.addLayout(right_column, stretch=4)

        main_layout.addWidget(content, stretch=1)

    def _go_prev_month(self):
        self._month -= 1
        if self._month < 1:
            self._month = 12
            self._year -= 1
        self._refresh()

    def _go_next_month(self):
        self._month += 1
        if self._month > 12:
            self._month = 1
            self._year += 1
        self._refresh()

    def _refresh_calendar(self):
        # Update Month Label Text
        month_name = calendar.month_name[self._month]
        self._month_label.setText(f"{month_name} {self._year}")

        # Clear old dates grid
        while self._dates_grid.count():
            item = self._dates_grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        # Calculate exact dates grid range (Monday start, 6 weeks total = 42 cells)
        first_day = date(self._year, self._month, 1)
        start_date = first_day - timedelta(days=first_day.weekday())

        for idx in range(42):
            target_date = start_date + timedelta(days=idx)
            row = idx // 7
            col = idx % 7

            is_current_month = (target_date.month == self._month)
            
            # Fast check if date contains tasks
            tasks_list = task_manager.list_tasks(target_date)
            has_tasks = len(tasks_list) > 0

            is_selected = (target_date == self._selected_date)

            btn = DayButton(target_date, is_current_month, has_tasks, is_selected)
            btn.clicked.connect(lambda checked=False, d=target_date: self._on_date_clicked(d))
            self._dates_grid.addWidget(btn, row, col)

    def _on_date_clicked(self, clicked_date: date):
        self._selected_date = clicked_date
        self._refresh()

    def _populate_subject_combo(self):
        self._subject_combo.clear()
        self._subject_combo.addItem("📂  No Subject", None)
        
        subjects = subject_manager.list_subjects()
        for s in subjects:
            self._subject_combo.addItem(f"🏷️  {s.name}", s.id)

    def _refresh_day_view(self):
        # Repopulate drop-down items safely
        self._populate_subject_combo()

        # Set card title
        day_str = self._selected_date.strftime("%A, %b %d")
        self._day_title.setText(f"📋  {day_str}")

        # Clear old tasks
        while self._task_inner_layout.count():
            item = self._task_inner_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        # Fetch tasks solely for the selected date
        tasks = task_manager.list_tasks(self._selected_date, exclude_dumped=True)

        if not tasks:
            empty_lbl = QLabel("No tasks for this day. Plan a task below!")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: rgba(203, 170, 205, 0.45); font-size: 13px; font-style: italic; margin-top: 50px;")
            self._task_inner_layout.addWidget(empty_lbl)
        else:
            for t in tasks:
                task_strip = QFrame()
                task_strip.setStyleSheet("""
                    QFrame {
                        background: rgba(255, 255, 255, 0.03);
                        border: 1px solid rgba(255, 255, 255, 0.04);
                        border-radius: 8px;
                    }
                    QFrame:hover {
                        background: rgba(255, 255, 255, 0.06);
                    }
                """)
                strip_layout = QHBoxLayout(task_strip)
                strip_layout.setContentsMargins(12, 10, 12, 10)
                strip_layout.setSpacing(12)

                # Custom Checkbox
                chk = QCheckBox()
                chk.setChecked(t.is_completed)
                chk.setCursor(Qt.CursorShape.PointingHandCursor)
                chk.setStyleSheet("""
                    QCheckBox::indicator {
                        width: 18px;
                        height: 18px;
                    }
                """)
                chk.stateChanged.connect(lambda state, tid=t.id: self._toggle_task_complete(tid))
                strip_layout.addWidget(chk)

                # Text/Info column
                text_col = QVBoxLayout()
                text_col.setSpacing(4)
                text_col.setContentsMargins(0, 0, 0, 0)

                # Task Title
                lbl = QLabel(t.title)
                lbl.setWordWrap(True)
                if t.is_completed:
                    lbl.setStyleSheet("color: rgba(203, 170, 205, 0.4); text-decoration: line-through; font-size: 13.5px;")
                else:
                    lbl.setStyleSheet("color: #ECFDF5; font-size: 13.5px; font-weight: 500;")
                text_col.addWidget(lbl)

                # Badges row (Subject + Priority)
                badges_row = QHBoxLayout()
                badges_row.setSpacing(6)
                badges_row.setAlignment(Qt.AlignmentFlag.AlignLeft)

                # Priority Badge
                pri_colors = {
                    "high": ("#FECACA", "#EF4444"),  # (bg, text)
                    "med": ("#FEF3C7", "#D97706"),
                    "low": ("#D1FAE5", "#059669")
                }
                bg_hex, fg_hex = pri_colors.get(t.priority, ("#FEF3C7", "#D97706"))
                
                pri_lbl = QLabel(t.priority.upper())
                pri_lbl.setStyleSheet(f"""
                    padding: 2px 6px;
                    background-color: {hex_to_rgba(bg_hex, 0.15)};
                    color: {fg_hex};
                    border-radius: 4px;
                    font-size: 9px;
                    font-weight: 800;
                    border: 1px solid {hex_to_rgba(bg_hex, 0.3)};
                """)
                badges_row.addWidget(pri_lbl)

                # Subject Badge
                if t.subject_id:
                    s = subject_manager.get_subject(t.subject_id)
                    if s:
                        sub_lbl = QLabel(s.name.upper())
                        sub_lbl.setStyleSheet(f"""
                            padding: 2px 6px;
                            background-color: {hex_to_rgba(s.color_hex, 0.15)};
                            color: {s.color_hex};
                            border-radius: 4px;
                            font-size: 9px;
                            font-weight: 800;
                            border: 1px solid {hex_to_rgba(s.color_hex, 0.3)};
                        """)
                        badges_row.addWidget(sub_lbl)

                text_col.addLayout(badges_row)
                strip_layout.addLayout(text_col, stretch=1)

                # Delete Button
                del_btn = QPushButton("✕")
                del_btn.setFixedSize(24, 24)
                del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                del_btn.setStyleSheet("""
                    QPushButton {
                        color: rgba(255, 107, 107, 0.5);
                        background: transparent;
                        border: none;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        color: rgba(255, 107, 107, 0.95);
                    }
                """)
                del_btn.clicked.connect(lambda checked=False, tid=t.id: self._delete_task(tid))
                strip_layout.addWidget(del_btn)

                self._task_inner_layout.addWidget(task_strip)

    def _create_quick_task(self):
        text = self._task_input.text().strip()
        if not text:
            return
        
        # Get subject selection safely
        sub_idx = self._subject_combo.currentIndex()
        subject_id = self._subject_combo.itemData(sub_idx)

        # Get priority selection safely
        pri_idx = self._priority_combo.currentIndex()
        priority = self._priority_combo.itemData(pri_idx) or "med"

        # Create task bound to selected date
        task_manager.create_task(
            title=text,
            target_date=self._selected_date,
            subject_id=subject_id,
            priority=priority
        )
        self._task_input.clear()
        self._refresh()

    def _toggle_task_complete(self, task_id: int):
        task_manager.toggle_task(task_id)
        self._refresh()

    def _delete_task(self, task_id: int):
        task_manager.delete_task(task_id)
        self._refresh()

    def _refresh(self):
        self.setUpdatesEnabled(False)
        try:
            self._refresh_calendar()
            self._refresh_day_view()
        finally:
            self.setUpdatesEnabled(True)
            self.update()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh()
