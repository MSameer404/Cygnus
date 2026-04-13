# src/app/ui/todo_page.py
"""To-do list page with date selector, add input, and task list."""

from datetime import date, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core import subject_manager, todo_manager
from app.data.models import TodoItem


class TodoPage(QWidget):
    """To-do list with date navigation, add input, and completion tracking."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_date = date.today()
        self._setup_ui()

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

        # ---------- Date Navigation ----------
        nav = QHBoxLayout()

        prev_btn = QPushButton("Prev")
        prev_btn.setProperty("class", "ghost")
        prev_btn.setFixedHeight(36)
        prev_btn.setStyleSheet(
            "font-size: 14px; font-weight: bold;"
        )
        prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        prev_btn.clicked.connect(self._prev_day)
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
        next_btn.setStyleSheet(
            "font-size: 14px; font-weight: bold;"
        )
        next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        next_btn.clicked.connect(self._next_day)
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

        add_btn = QPushButton("+ Add")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_todo)
        add_layout.addWidget(add_btn)

        layout.addWidget(add_frame)

        # ---------- Todo List ----------
        self._todo_container = QVBoxLayout()
        self._todo_container.setSpacing(6)
        self._todo_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addLayout(self._todo_container)

        layout.addStretch()

        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _prev_day(self):
        self._current_date -= timedelta(days=1)
        self._refresh()

    def _next_day(self):
        self._current_date += timedelta(days=1)
        self._refresh()

    def _go_today(self):
        self._current_date = date.today()
        self._refresh()

    def _add_todo(self):
        text = self._input.text().strip()
        if not text:
            return

        subject_id = self._subject_combo.currentData()
        todo_manager.create_todo(
            title=text,
            target_date=self._current_date,
            subject_id=subject_id,
        )
        self._input.clear()
        self._refresh()

    def _refresh(self):
        """Reload todos for current date."""
        self._date_label.setText(self._current_date.strftime("%A, %B %d, %Y"))

        # Clear list
        while self._todo_container.count():
            item = self._todo_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        todos = todo_manager.list_todos(target_date=self._current_date)
        completed = sum(1 for t in todos if t.is_completed)
        total = len(todos)

        # Update progress
        pct = (completed / total * 100) if total > 0 else 0
        self._progress_label.setText(f"{completed} / {total} completed")
        self._progress_bar.setValue(int(pct))
        self._pct_label.setText(f"{pct:.0f}%")

        if not todos:
            empty = QLabel("No tasks for this day. Add one above!")
            empty.setProperty("class", "muted")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("padding: 30px;")
            self._todo_container.addWidget(empty)
            return

        # Pending items first, then completed
        for todo in todos:
            card = self._make_todo_card(todo)
            self._todo_container.addWidget(card)

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
        todo_manager.delete_todo(todo_id)
        self._refresh()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh()
