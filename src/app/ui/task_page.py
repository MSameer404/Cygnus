# src/app/ui/task_page.py
"""Task dashboard: stats, work table, filtered task list, and create dialog."""

from __future__ import annotations

from datetime import date
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core import subject_manager, task_manager
from app.core.events import app_events
from app.ui.widgets.create_task_dialog import CreateTaskDialog


class TaskPage(QWidget):
    """Modern task dashboard with work table and filtered backlog."""

    _FILTER_ALL = "all"
    _FILTER_PENDING = "pending"
    _FILTER_OVERDUE = "overdue"
    _FILTER_COMPLETED = "completed"
    _FILTER_DUMP = "dump"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tasks: list[dict[str, Any]] = []
        self._list_filter = self._FILTER_ALL
        self._filter_buttons: dict[str, QPushButton] = {}
        self._setup_ui()
        app_events.data_reset.connect(self._on_data_reset)

    def _on_data_reset(self):
        self._list_filter = self._FILTER_ALL
        self._set_filter_active(self._FILTER_ALL)
        self._refresh()

    def _setup_ui(self):
        self.setObjectName("taskDashboard")
        self.setMinimumSize(900, 600)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 30, 40, 30)
        outer.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("Task list")
        title.setProperty("class", "task-page-title")
        header.addWidget(title)
        header.addStretch()
        create_btn = QPushButton("+ Create task")
        create_btn.setProperty("class", "task-create-btn")
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.clicked.connect(self._open_create_dialog)
        header.addWidget(create_btn)
        outer.addLayout(header)

        # Stats row
        stats = QHBoxLayout()
        stats.setSpacing(12)
        self._stat_pending = self._make_stat_card("Pending", "stat-pending")
        self._stat_overdue = self._make_stat_card("Overdue", "stat-overdue")
        self._stat_completed = self._make_stat_card("Completed", "stat-done")
        self._stat_dump = self._make_stat_card("Dump", "stat-dump")
        self._stat_total = self._make_stat_card("Total", "stat-total")
        for w in (
            self._stat_pending,
            self._stat_overdue,
            self._stat_completed,
            self._stat_dump,
            self._stat_total,
        ):
            stats.addWidget(w)
        outer.addLayout(stats)

        # Split panels
        split = QHBoxLayout()
        split.setSpacing(16)

        self._work_frame = QFrame()
        self._work_frame.setProperty("class", "task-panel card")
        work_outer = QVBoxLayout(self._work_frame)
        work_outer.setContentsMargins(16, 14, 16, 14)
        work_outer.setSpacing(10)
        wh = QLabel("Work table")
        wh.setProperty("class", "task-panel-title")
        work_outer.addWidget(wh)
        self._work_scroll = QScrollArea()
        self._work_scroll.setWidgetResizable(True)
        self._work_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._work_inner = QWidget()
        self._work_layout = QVBoxLayout(self._work_inner)
        self._work_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._work_layout.setSpacing(8)
        self._work_scroll.setWidget(self._work_inner)
        work_outer.addWidget(self._work_scroll, stretch=1)
        split.addWidget(self._work_frame, stretch=4)

        self._list_frame = QFrame()
        self._list_frame.setProperty("class", "task-panel card")
        list_outer = QVBoxLayout(self._list_frame)
        list_outer.setContentsMargins(16, 14, 16, 14)
        list_outer.setSpacing(10)

        tabs = QHBoxLayout()
        tabs.setSpacing(8)
        for key, label in (
            (self._FILTER_ALL, "All"),
            (self._FILTER_PENDING, "Pending"),
            (self._FILTER_OVERDUE, "Overdue"),
            (self._FILTER_COMPLETED, "Completed"),
            (self._FILTER_DUMP, "Dump"),
        ):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("class", "task-filter-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._on_filter_clicked(k))
            self._filter_buttons[key] = btn
            tabs.addWidget(btn)
        tabs.addStretch()
        list_outer.addLayout(tabs)
        self._set_filter_active(self._FILTER_ALL)

        self._task_scroll = QScrollArea()
        self._task_scroll.setWidgetResizable(True)
        self._task_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._task_inner = QWidget()
        self._task_layout = QVBoxLayout(self._task_inner)
        self._task_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._task_layout.setSpacing(10)
        self._task_scroll.setWidget(self._task_inner)
        list_outer.addWidget(self._task_scroll, stretch=1)
        split.addWidget(self._list_frame, stretch=6)

        outer.addLayout(split, stretch=1)

    def _make_stat_card(self, caption: str, value_class: str) -> QFrame:
        fr = QFrame()
        fr.setProperty("class", "task-stat-card card")
        lay = QVBoxLayout(fr)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)
        val = QLabel("0")
        val.setProperty("class", f"task-stat-value {value_class}")
        cap = QLabel(caption)
        cap.setProperty("class", "task-stat-caption")
        lay.addWidget(val)
        lay.addWidget(cap)
        fr._value_label = val  # type: ignore[attr-defined]
        return fr

    def _set_filter_active(self, key: str):
        self._list_filter = key
        for k, btn in self._filter_buttons.items():
            btn.setChecked(k == key)

    def _on_filter_clicked(self, key: str):
        self._set_filter_active(key)
        self._render_task_list()

    def _open_create_dialog(self):
        dlg = CreateTaskDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            title, subject_id, priority, due = dlg.values()
            task_manager.create_task(
                title=title,
                target_date=due,
                subject_id=subject_id,
                priority=priority,
            )
            self._refresh()

    def _rebuild_cache(self):
        today = date.today()
        self._tasks = []
        for t in task_manager.list_all_tasks():
            subject_name = ""
            if t.subject_id:
                s = subject_manager.get_subject(t.subject_id)
                if s:
                    subject_name = s.name
            overdue = (
                not t.is_completed
                and not t.is_dumped
                and t.target_date < today
            )
            self._tasks.append(
                {
                    "id": t.id,
                    "title": t.title,
                    "subject_id": t.subject_id,
                    "subject_name": subject_name,
                    "target_date": t.target_date,
                    "priority": t.priority or "med",
                    "is_completed": t.is_completed,
                    "in_work": t.in_work,
                    "is_dumped": t.is_dumped,
                    "overdue": overdue,
                }
            )

    def _update_stats(self):
        today = date.today()
        total = len(self._tasks)
        pending = overdue = completed = dump = 0
        for r in self._tasks:
            if r["is_dumped"]:
                dump += 1
                continue
            if r["is_completed"]:
                completed += 1
                continue
            if r["target_date"] < today:
                overdue += 1
            else:
                pending += 1

        self._stat_pending._value_label.setText(str(pending))  # type: ignore[attr-defined]
        self._stat_overdue._value_label.setText(str(overdue))  # type: ignore[attr-defined]
        self._stat_completed._value_label.setText(str(completed))  # type: ignore[attr-defined]
        self._stat_dump._value_label.setText(str(dump))  # type: ignore[attr-defined]
        self._stat_total._value_label.setText(str(total))  # type: ignore[attr-defined]

    def _status_text(self, row: dict[str, Any]) -> str:
        if row["is_dumped"]:
            return "Dump"
        if row["is_completed"]:
            return "Completed"
        if row["overdue"]:
            return "Overdue"
        return "Pending"

    def _clear_layout(self, layout: QVBoxLayout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _render_work_table(self):
        self._clear_layout(self._work_layout)
        rows = [
            r
            for r in self._tasks
            if r["in_work"] and not r["is_completed"]
        ]
        if not rows:
            empty = QLabel("Nothing in progress. Add a task from the list.")
            empty.setProperty("class", "muted")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setWordWrap(True)
            self._work_layout.addWidget(empty)
            return
        for row in rows:
            self._work_layout.addWidget(self._make_work_row(row))

    def _make_work_row(self, row: dict[str, Any]) -> QFrame:
        card = QFrame()
        card.setProperty("class", "task-work-row card")
        h = QHBoxLayout(card)
        h.setContentsMargins(10, 8, 10, 8)
        mid = QVBoxLayout()
        mid.setSpacing(2)
        t = QLabel(row["title"])
        t.setWordWrap(True)
        t.setProperty("class", "task-work-title")
        mid.addWidget(t)
        sub = QLabel(
            f"{row['subject_name'] or '—'} · Due {row['target_date'].strftime('%Y-%m-%d')}"
        )
        sub.setProperty("class", "task-meta")
        mid.addWidget(sub)
        h.addLayout(mid, stretch=1)
        done_btn = QPushButton("Mark Done")
        done_btn.setProperty("class", "task-secondary-btn")
        done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tid = row["id"]
        done_btn.clicked.connect(lambda _=False, i=tid: self._mark_done(i))
        h.addWidget(done_btn)
        rm_btn = QPushButton("Remove")
        rm_btn.setProperty("class", "task-ghost-btn")
        rm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rm_btn.clicked.connect(lambda _=False, i=tid: self._remove_from_work(i))
        h.addWidget(rm_btn)
        return card

    def _mark_done(self, task_id: int):
        task_manager.update_task_fields(
            task_id, is_completed=True, in_work=False
        )
        self._refresh()

    def _remove_from_work(self, task_id: int):
        task_manager.update_task_fields(task_id, in_work=False)
        self._refresh()

    def _row_matches_list_filter(self, row: dict[str, Any]) -> bool:
        today = date.today()
        if row["in_work"]:
            return False
        if self._list_filter == self._FILTER_ALL:
            return True
        if self._list_filter == self._FILTER_COMPLETED:
            return row["is_completed"]
        if self._list_filter == self._FILTER_DUMP:
            return row["is_dumped"]
        if row["is_completed"] or row["is_dumped"]:
            return False
        if self._list_filter == self._FILTER_OVERDUE:
            return row["target_date"] < today
        if self._list_filter == self._FILTER_PENDING:
            return row["target_date"] >= today
        return True

    def _render_task_list(self):
        self._clear_layout(self._task_layout)
        rows = [r for r in self._tasks if self._row_matches_list_filter(r)]
        if not rows:
            empty = QLabel("No tasks here.")
            empty.setProperty("class", "muted")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._task_layout.addWidget(empty)
            return
        for row in rows:
            self._task_layout.addWidget(self._make_task_card(row))

    def _make_task_card(self, row: dict[str, Any]) -> QFrame:
        card = QFrame()
        card.setProperty("class", "task-task-card card")
        v = QVBoxLayout(card)
        v.setContentsMargins(12, 10, 12, 10)
        v.setSpacing(8)

        top = QHBoxLayout()
        title = QLabel(row["title"])
        title.setWordWrap(True)
        title.setProperty("class", "task-task-title")
        top.addWidget(title, stretch=1)
        v.addLayout(top)

        subj = QLabel(row["subject_name"] or "No subject")
        subj.setProperty("class", "task-meta")
        v.addWidget(subj)

        due = QLabel(f"Due {row['target_date'].strftime('%Y-%m-%d')}")
        due.setProperty("class", "task-meta")
        v.addWidget(due)

        pills = QHBoxLayout()
        pills.setSpacing(6)
        pr = QLabel(row["priority"].title())
        pr.setProperty("class", f"task-pill-priority-{row['priority']}")
        pills.addWidget(pr)
        st = QLabel(self._status_text(row))
        st.setProperty("class", f"task-pill-status-{self._status_slug(row)}")
        pills.addWidget(st)
        pills.addStretch()
        v.addLayout(pills)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        tid = row["id"]
        can_work = (
            not row["is_completed"]
            and not row["is_dumped"]
            and not row["in_work"]
        )
        if can_work:
            aw = QPushButton("+ Add to work table")
            aw.setProperty("class", "task-accent-outline-btn")
            aw.setCursor(Qt.CursorShape.PointingHandCursor)
            aw.clicked.connect(lambda _=False, i=tid: self._add_to_work(i))
            actions.addWidget(aw)
        if not row["is_dumped"] and not row["is_completed"]:
            dump_btn = QPushButton("Move to dump")
            dump_btn.setProperty("class", "task-ghost-btn")
            dump_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            dump_btn.clicked.connect(lambda _=False, i=tid: self._move_to_dump(i))
            actions.addWidget(dump_btn)
        actions.addStretch()
        v.addLayout(actions)
        return card

    def _status_slug(self, row: dict[str, Any]) -> str:
        if row["is_dumped"]:
            return "dump"
        if row["is_completed"]:
            return "completed"
        if row["overdue"]:
            return "overdue"
        return "pending"

    def _add_to_work(self, task_id: int):
        task_manager.update_task_fields(task_id, in_work=True)
        self._refresh()

    def _move_to_dump(self, task_id: int):
        task_manager.update_task_fields(
            task_id, is_dumped=True, in_work=False
        )
        self._refresh()

    def _refresh(self):
        self._rebuild_cache()
        self._update_stats()
        self._render_work_table()
        self._render_task_list()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh()
