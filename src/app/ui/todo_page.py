# src/app/ui/todo_page.py
"""To-do list page with Daily / Weekly views, date navigation, and task management."""

from datetime import date, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTabBar,
    QVBoxLayout,
    QWidget,
)

from app.core import subject_manager, todo_manager
from app.core.events import app_events
from app.data.models import TodoItem


class TodoPage(QWidget):
    """To-do list with Daily / Weekly tabs, date navigation, and completion tracking."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_date = date.today()
        self._current_tab = 0  # 0=Daily, 1=Weekly
        self._setup_ui()
        app_events.data_reset.connect(self._on_data_reset)

    def _on_data_reset(self):
        """Refresh todos when all data is reset."""
        self._current_date = date.today()
        self._current_tab = 0
        self._tab_bar.setCurrentIndex(0)
        self._refresh()

    # ─── helpers ───

    @staticmethod
    def _week_start(d: date) -> date:
        """Return Monday of the week containing *d*."""
        return d - timedelta(days=d.weekday())

    @staticmethod
    def _week_end(d: date) -> date:
        """Return Sunday of the week containing *d*."""
        return d + timedelta(days=6 - d.weekday())

    # ─── UI construction ───

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # ---------- Header ----------
        header = QHBoxLayout()
        title = QLabel("To-Do List")
        title.setProperty("class", "heading")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # ---------- Tab Bar (Daily / Weekly) ----------
        self._tab_bar = QTabBar()
        self._tab_bar.addTab("Daily")
        self._tab_bar.addTab("Weekly")
        self._tab_bar.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self._tab_bar)

        # ---------- Date Navigation ----------
        nav = QHBoxLayout()

        prev_btn = QPushButton("Prev")
        prev_btn.setProperty("class", "ghost")
        prev_btn.setFixedHeight(36)
        prev_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        prev_btn.clicked.connect(self._prev)
        nav.addWidget(prev_btn)

        self._date_label = QLabel()
        self._date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._date_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        nav.addWidget(self._date_label, stretch=1)

        today_btn = QPushButton("Today")
        today_btn.setProperty("class", "secondary")
        today_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        today_btn.clicked.connect(self._go_today)
        nav.addWidget(today_btn)

        next_btn = QPushButton("Next")
        next_btn.setProperty("class", "ghost")
        next_btn.setFixedHeight(36)
        next_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        next_btn.clicked.connect(self._next)
        nav.addWidget(next_btn)

        layout.addLayout(nav)

        # ---------- Progress ----------
        progress_frame = QFrame()
        progress_frame.setProperty("class", "card")
        progress_layout = QHBoxLayout(progress_frame)
        progress_layout.setContentsMargins(16, 12, 16, 12)

        self._progress_label = QLabel("0 / 0 completed")
        self._progress_label.setStyleSheet("font-size: 13px;")
        progress_layout.addWidget(self._progress_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setMaximum(100)
        self._progress_bar.setFixedWidth(200)
        progress_layout.addWidget(self._progress_bar)

        self._pct_label = QLabel("0%")
        self._pct_label.setStyleSheet("font-weight: bold; color: #6C5CE7;")
        progress_layout.addWidget(self._pct_label)

        layout.addWidget(progress_frame)

        # ---------- Add Todo Input ----------
        add_frame = QFrame()
        add_frame.setProperty("class", "card")
        add_layout = QHBoxLayout(add_frame)
        add_layout.setContentsMargins(12, 8, 12, 8)
        add_layout.setSpacing(8)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Add a new task...")
        self._input.returnPressed.connect(self._add_todo)
        add_layout.addWidget(self._input, stretch=1)

        # Optional subject selector
        self._subject_combo = QComboBox()
        self._subject_combo.addItem("No subject", None)
        for s in subject_manager.list_subjects():
            self._subject_combo.addItem(f"● {s.name}", s.id)
        self._subject_combo.setFixedWidth(160)
        add_layout.addWidget(self._subject_combo)

        # Day selector (only visible in weekly mode)
        self._day_combo = QComboBox()
        self._day_combo.setFixedWidth(120)
        self._day_combo.hide()
        add_layout.addWidget(self._day_combo)

        add_btn = QPushButton("+ Add")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_todo)
        add_layout.addWidget(add_btn)

        layout.addWidget(add_frame)

        # ---------- Todo Content Area ----------
        # This container holds EITHER the daily list OR the weekly grid
        self._todo_container = QVBoxLayout()
        self._todo_container.setSpacing(6)
        self._todo_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addLayout(self._todo_container)

        layout.addStretch()

        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ─── Tab switching ───

    def _on_tab_changed(self, index: int):
        self._current_tab = index
        self._current_date = date.today()
        # Toggle day combo visibility
        self._day_combo.setVisible(index == 1)
        self._refresh()

    # ─── Navigation ───

    def _prev(self):
        if self._current_tab == 0:
            self._current_date -= timedelta(days=1)
        else:
            self._current_date -= timedelta(weeks=1)
        self._refresh()

    def _next(self):
        if self._current_tab == 0:
            self._current_date += timedelta(days=1)
        else:
            self._current_date += timedelta(weeks=1)
        self._refresh()

    def _go_today(self):
        self._current_date = date.today()
        self._refresh()

    # ─── Add todo ───

    def _add_todo(self):
        text = self._input.text().strip()
        if not text:
            return

        subject_id = self._subject_combo.currentData()

        if self._current_tab == 1:
            # Weekly mode — use the day combo to pick the target date
            target = self._day_combo.currentData()
            if target is None:
                target = self._current_date
        else:
            target = self._current_date

        todo_manager.create_todo(
            title=text,
            target_date=target,
            subject_id=subject_id,
        )
        self._input.clear()
        self._refresh()

    # ─── Refresh ───

    def _refresh(self):
        if self._current_tab == 0:
            self._refresh_daily()
        else:
            self._refresh_weekly()

    def _refresh_daily(self):
        """Reload todos for a single day."""
        self._date_label.setText(self._current_date.strftime("%A, %B %d, %Y"))

        # Clear container
        self._clear_container()

        todos = todo_manager.list_todos(target_date=self._current_date)
        completed = sum(1 for t in todos if t.is_completed)
        total = len(todos)

        self._update_progress(completed, total)

        if not todos:
            empty = QLabel("No tasks for this day. Add one above!")
            empty.setProperty("class", "muted")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("padding: 30px;")
            self._todo_container.addWidget(empty)
            return

        for todo in todos:
            card = self._make_todo_card(todo)
            self._todo_container.addWidget(card)

    def _refresh_weekly(self):
        """Reload todos for a full Mon–Sun week."""
        ws = self._week_start(self._current_date)
        we = self._week_end(self._current_date)
        self._date_label.setText(
            f"{ws.strftime('%b %d')} – {we.strftime('%b %d, %Y')}"
        )

        # Populate day selector combo
        self._day_combo.blockSignals(True)
        self._day_combo.clear()
        today = date.today()
        default_idx = 0
        for i in range(7):
            d = ws + timedelta(days=i)
            label = d.strftime("%a %d")
            if d == today:
                label += " ★"
                default_idx = i
            self._day_combo.addItem(label, d)
        self._day_combo.setCurrentIndex(default_idx)
        self._day_combo.blockSignals(False)

        # Clear container
        self._clear_container()

        all_todos = todo_manager.list_todos_for_range(ws, we)
        completed = sum(1 for t in all_todos if t.is_completed)
        total = len(all_todos)
        self._update_progress(completed, total)

        # Build weekly grid: 7 columns
        week_widget = QWidget()
        week_layout = QHBoxLayout(week_widget)
        week_layout.setContentsMargins(0, 0, 0, 0)
        week_layout.setSpacing(10)

        # Group todos by date
        by_date: dict[date, list[TodoItem]] = {}
        for i in range(7):
            by_date[ws + timedelta(days=i)] = []
        for t in all_todos:
            if t.target_date in by_date:
                by_date[t.target_date].append(t)

        for i in range(7):
            d = ws + timedelta(days=i)
            col = self._make_day_column(d, by_date[d])
            week_layout.addWidget(col)

        self._todo_container.addWidget(week_widget)

    def _make_day_column(self, d: date, todos: list[TodoItem]) -> QFrame:
        """Create a vertical column for one day in the weekly view."""
        col = QFrame()
        col.setProperty("class", "card")
        col.setMinimumWidth(120)
        layout = QVBoxLayout(col)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # Day header
        is_today = d == date.today()
        header = QLabel(d.strftime("%a\n%d"))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if is_today:
            header.setStyleSheet(
                "font-weight: bold; font-size: 14px; color: #6C5CE7; "
                "background-color: rgba(108, 92, 231, 0.15); "
                "border-radius: 8px; padding: 6px;"
            )
        else:
            header.setStyleSheet(
                "font-weight: bold; font-size: 13px; color: #EAEAF0; padding: 6px;"
            )
        layout.addWidget(header)

        # Mini progress
        done = sum(1 for t in todos if t.is_completed)
        total = len(todos)
        if total > 0:
            pct_label = QLabel(f"{done}/{total}")
            pct_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pct_label.setStyleSheet("font-size: 11px; color: #8B8BA0;")
            layout.addWidget(pct_label)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("border: 1px solid rgba(255,255,255,0.06);")
        layout.addWidget(sep)

        if not todos:
            empty = QLabel("—")
            empty.setProperty("class", "muted")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("padding: 12px 0; font-size: 12px;")
            layout.addWidget(empty)
        else:
            for todo in todos:
                row = self._make_compact_todo(todo)
                layout.addWidget(row)

        layout.addStretch()
        return col

    def _make_compact_todo(self, todo: TodoItem) -> QWidget:
        """Compact checkbox + title for weekly column view."""
        row_widget = QWidget()
        row = QHBoxLayout(row_widget)
        row.setContentsMargins(0, 2, 0, 2)
        row.setSpacing(4)

        cb = QCheckBox()
        cb.setChecked(todo.is_completed)
        cb.stateChanged.connect(lambda state, t_id=todo.id: self._toggle(t_id))
        row.addWidget(cb)

        title = QLabel(todo.title)
        title.setWordWrap(True)
        if todo.is_completed:
            title.setStyleSheet("text-decoration: line-through; color: #8B8BA0; font-size: 12px;")
        else:
            title.setStyleSheet("font-size: 12px;")
        row.addWidget(title, stretch=1)

        return row_widget

    # ─── Shared helpers ───

    def _clear_container(self):
        while self._todo_container.count():
            item = self._todo_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _update_progress(self, completed: int, total: int):
        pct = (completed / total * 100) if total > 0 else 0
        self._progress_label.setText(f"{completed} / {total} completed")
        self._progress_bar.setValue(int(pct))
        self._pct_label.setText(f"{pct:.0f}%")

    def _make_todo_card(self, todo: TodoItem) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        row = QHBoxLayout(card)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(10)

        # Checkbox
        cb = QCheckBox()
        cb.setChecked(todo.is_completed)
        cb.stateChanged.connect(lambda state, t_id=todo.id: self._toggle(t_id))
        row.addWidget(cb)

        # Subject color dot
        if todo.subject_id:
            subj = subject_manager.get_subject(todo.subject_id)
            if subj:
                dot = QLabel("●")
                dot.setStyleSheet(f"color: {subj.color_hex}; font-size: 14px;")
                dot.setFixedWidth(16)
                row.addWidget(dot)

        # Title
        title = QLabel(todo.title)
        if todo.is_completed:
            title.setStyleSheet("text-decoration: line-through; color: #8B8BA0;")
        else:
            title.setStyleSheet("font-size: 14px;")
        row.addWidget(title, stretch=1)

        # Delete
        del_btn = QPushButton("✕")
        del_btn.setProperty("class", "icon-btn")
        del_btn.setFixedSize(24, 24)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet("color: #FF6B6B; font-size: 12px;")
        del_btn.clicked.connect(lambda: self._delete(todo.id))
        row.addWidget(del_btn)

        return card

    def _toggle(self, todo_id: int):
        todo_manager.toggle_todo(todo_id)
        self._refresh()

    def _delete(self, todo_id: int):
        reply = QMessageBox.warning(
            self,
            "Delete Task",
            "Are you sure you want to delete this task?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            todo_manager.delete_todo(todo_id)
            self._refresh()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh()
