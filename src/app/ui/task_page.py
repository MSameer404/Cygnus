# src/app/ui/task_page.py
"""Task dashboard: stats, work table, filtered task list, and create dialog."""

from __future__ import annotations

from datetime import date
from typing import Any

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
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
        # Widget pools to prevent flickering
        self._work_row_pool: dict[int, QFrame] = {}
        self._task_card_pool: dict[int, QFrame] = {}
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
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ---------- Header Bar (consistent with other pages) ----------
        header = QWidget()
        header.setObjectName("pageHeader")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(16)

        title = QLabel("Task Tracker")
        title.setProperty("class", "heading")
        header_layout.addWidget(title)
        header_layout.addStretch()
        create_btn = QPushButton("+ Create task")
        create_btn.setProperty("class", "task-create-btn")
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.clicked.connect(self._open_create_dialog)
        header_layout.addWidget(create_btn)
        outer.addWidget(header)

        # Horizontal separator line below header (aligned with sidebar profile level)
        horizontal_line = QFrame()
        horizontal_line.setObjectName("headerSeparator")
        horizontal_line.setFrameShape(QFrame.Shape.HLine)
        horizontal_line.setFixedHeight(1)
        outer.addWidget(horizontal_line)

        # ---------- Content ----------
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setSpacing(16)

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
        content_layout.addLayout(stats)

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
        self._work_layout.setSpacing(6)
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
            (self._FILTER_PENDING, "Pending"),
            (self._FILTER_OVERDUE, "Overdue"),
        ):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("class", "task-filter-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._on_filter_clicked(k))
            self._filter_buttons[key] = btn
            tabs.addWidget(btn)

        tabs.addStretch()

        for key, label in (
            (self._FILTER_ALL, "All"),
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
        self._task_layout.setSpacing(6)
        self._task_scroll.setWidget(self._task_inner)
        list_outer.addWidget(self._task_scroll, stretch=1)
        split.addWidget(self._list_frame, stretch=6)

        content_layout.addLayout(split, stretch=1)
        outer.addWidget(content, stretch=1)

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
        # Defer render to let button check state settle visually
        QTimer.singleShot(0, self._render_task_list)

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
            subject_color = "#8B8BA0"
            if t.subject_id:
                s = subject_manager.get_subject(t.subject_id)
                if s:
                    subject_name = s.name
                    subject_color = s.color_hex
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
                    "subject_color": subject_color,
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
                w.hide()

    def _render_work_table(self):
        rows = [
            r
            for r in self._tasks
            if r["in_work"] and not r["is_completed"]
        ]
        active_ids = {r["id"] for r in rows}

        # Hide widgets for tasks no longer in work table
        for tid, widget in list(self._work_row_pool.items()):
            if tid not in active_ids:
                widget.hide()

        if not rows:
            # Check if empty label already exists
            has_empty = False
            for i in range(self._work_layout.count()):
                w = self._work_layout.itemAt(i).widget()
                if w and w.objectName() == "work_empty":
                    has_empty = True
                    w.show()
                    break
            if not has_empty:
                empty = QLabel("Nothing in progress. Add a task from the list.")
                empty.setObjectName("work_empty")
                empty.setProperty("class", "muted")
                empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty.setWordWrap(True)
                self._work_layout.addWidget(empty)
        else:
            # Hide empty label if exists
            for i in range(self._work_layout.count()):
                w = self._work_layout.itemAt(i).widget()
                if w and w.objectName() == "work_empty":
                    w.hide()
                    break
            # Reuse or create work row widgets
            for i, row in enumerate(rows):
                tid = row["id"]
                if tid in self._work_row_pool:
                    widget = self._work_row_pool[tid]
                    self._update_work_row(widget, row)
                else:
                    widget = self._make_work_row(row)
                    self._work_row_pool[tid] = widget
                    self._work_layout.addWidget(widget)
                widget.show()

    def _make_work_row(self, row: dict[str, Any]) -> QFrame:
        card = QFrame()
        card.setProperty("class", "task-work-row card")
        h = QHBoxLayout(card)
        h.setContentsMargins(8, 6, 10, 6)
        mid = QVBoxLayout()
        mid.setSpacing(2)

        title_lbl = QLabel()
        title_lbl.setObjectName("title")
        title_lbl.setWordWrap(True)
        title_lbl.setProperty("class", "task-work-title")
        mid.addWidget(title_lbl)

        sub_lbl = QLabel()
        sub_lbl.setObjectName("sub")
        sub_lbl.setProperty("class", "task-meta")
        mid.addWidget(sub_lbl)

        h.addLayout(mid, stretch=1)

        done_btn = QPushButton("Mark Done")
        done_btn.setObjectName("done_btn")
        done_btn.setProperty("class", "task-secondary-btn")
        done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        h.addWidget(done_btn)

        rm_btn = QPushButton("Remove")
        rm_btn.setObjectName("rm_btn")
        rm_btn.setProperty("class", "task-ghost-btn")
        rm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        h.addWidget(rm_btn)

        self._update_work_row(card, row)
        return card

    def _update_work_row(self, card: QFrame, row: dict[str, Any]) -> None:
        title_lbl = card.findChild(QLabel, "title")
        sub_lbl = card.findChild(QLabel, "sub")
        done_btn = card.findChild(QPushButton, "done_btn")
        rm_btn = card.findChild(QPushButton, "rm_btn")

        if title_lbl:
            title_lbl.setText(row["title"])
        if sub_lbl:
            sub_lbl.setText(
                f"{row['subject_name'] or '—'} · Due {row['target_date'].strftime('%Y-%m-%d')}"
            )

        tid = row["id"]
        if done_btn:
            done_btn.clicked.disconnect() if done_btn.receivers(done_btn.clicked) else None
            done_btn.clicked.connect(lambda _=False, i=tid: self._mark_done(i))
        if rm_btn:
            try:
                rm_btn.clicked.disconnect()
            except:
                pass
            rm_btn.clicked.connect(lambda _=False, i=tid: self._remove_from_work(i))

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
        rows = [r for r in self._tasks if self._row_matches_list_filter(r)]
        active_ids = {r["id"] for r in rows}

        # Hide widgets for tasks no longer matching filter
        for tid, widget in list(self._task_card_pool.items()):
            if tid not in active_ids:
                widget.hide()

        if not rows:
            # Check if empty label already exists
            has_empty = False
            for i in range(self._task_layout.count()):
                w = self._task_layout.itemAt(i).widget()
                if w and w.objectName() == "list_empty":
                    has_empty = True
                    w.show()
                    break
            if not has_empty:
                empty = QLabel("No tasks here.")
                empty.setObjectName("list_empty")
                empty.setProperty("class", "muted")
                empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._task_layout.addWidget(empty)
        else:
            # Hide empty label if exists
            for i in range(self._task_layout.count()):
                w = self._task_layout.itemAt(i).widget()
                if w and w.objectName() == "list_empty":
                    w.hide()
                    break
            # Reuse or create task card widgets
            for i, row in enumerate(rows):
                tid = row["id"]
                if tid in self._task_card_pool:
                    widget = self._task_card_pool[tid]
                    self._update_task_card(widget, row)
                else:
                    widget = self._make_task_card(row)
                    self._task_card_pool[tid] = widget
                    self._task_layout.addWidget(widget)
                widget.show()

    def _make_task_card(self, row: dict[str, Any]) -> QFrame:
        card = QFrame()
        card.setProperty("class", "task-task-card card")
        body = QHBoxLayout(card)
        body.setContentsMargins(12, 10, 12, 10)
        body.setSpacing(16)

        # Left: Title and Subject
        left_widget = QWidget()
        left_widget.setObjectName("left_widget")
        left = QVBoxLayout(left_widget)
        left.setSpacing(4)
        left.setContentsMargins(0, 0, 0, 0)

        title = QLabel()
        title.setObjectName("title")
        title.setWordWrap(True)
        title.setStyleSheet("font-size: 15px; font-weight: 500; color: #EAEAF0;")
        left.addWidget(title)

        subj = QLabel()
        subj.setObjectName("subject")
        left.addWidget(subj)
        left_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        body.addWidget(left_widget, stretch=1)

        # Middle: Priority pill + Date + Status pill
        middle_widget = QWidget()
        middle_widget.setObjectName("middle_widget")
        middle = QHBoxLayout(middle_widget)
        middle.setSpacing(8)
        middle.setContentsMargins(0, 0, 0, 0)
        middle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        middle_widget.setMinimumWidth(240)
        middle_widget.setMaximumWidth(280)

        pr = QLabel()
        pr.setObjectName("priority")
        pr.setMinimumWidth(50)
        pr.setMaximumWidth(60)
        pr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        middle.addWidget(pr)

        due = QLabel()
        due.setObjectName("due_date")
        due.setStyleSheet("font-size: 12px; color: #8B8BA0;")
        due.setMinimumWidth(80)
        due.setMaximumWidth(90)
        due.setAlignment(Qt.AlignmentFlag.AlignCenter)
        middle.addWidget(due)

        st = QLabel()
        st.setObjectName("status")
        st.setMinimumWidth(90)
        st.setMaximumWidth(100)
        st.setAlignment(Qt.AlignmentFlag.AlignCenter)
        middle.addWidget(st)

        body.addWidget(middle_widget)

        # Right: Action buttons
        right_widget = QWidget()
        right_widget.setObjectName("right_widget")
        right = QHBoxLayout(right_widget)
        right.setSpacing(8)
        right.setContentsMargins(0, 0, 0, 0)
        right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        right_widget.setMinimumWidth(80)
        right_widget.setMaximumWidth(80)

        add_btn = QPushButton("▶")
        add_btn.setObjectName("add_btn")
        add_btn.setProperty("class", "task-action-btn")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setFixedWidth(36)
        add_btn.setFixedHeight(32)
        add_btn.setToolTip("Add to workspace")
        right.addWidget(add_btn)

        dump_btn = QPushButton("🗑️")
        dump_btn.setObjectName("dump_btn")
        dump_btn.setProperty("class", "task-dump-btn")
        dump_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dump_btn.setFixedWidth(36)
        dump_btn.setFixedHeight(32)
        dump_btn.setToolTip("Move to dump")
        right.addWidget(dump_btn)

        body.addWidget(right_widget)

        self._update_task_card(card, row)
        return card

    def _update_task_card(self, card: QFrame, row: dict[str, Any]) -> None:
        title = card.findChild(QLabel, "title")
        subj = card.findChild(QLabel, "subject")
        pr = card.findChild(QLabel, "priority")
        due = card.findChild(QLabel, "due_date")
        st = card.findChild(QLabel, "status")
        add_btn = card.findChild(QPushButton, "add_btn")
        dump_btn = card.findChild(QPushButton, "dump_btn")

        if title:
            title.setText(row["title"].title())
        if subj:
            subj_name = row["subject_name"] or "No subject"
            subj.setText(subj_name)
            subj.setStyleSheet(f"font-size: 12px; color: {row['subject_color']}; font-weight: 500;")
        if pr:
            pr.setText(row["priority"].upper())
            pr.setProperty("class", f"task-pill-priority-{row['priority']}")
            pr.style().unpolish(pr)
            pr.style().polish(pr)
        if due:
            due.setText(row["target_date"].strftime("%d %b %Y"))
        if st:
            st.setText(self._status_text(row).upper())
            st.setProperty("class", f"task-pill-status-{self._status_slug(row)}")
            st.style().unpolish(st)
            st.style().polish(st)

        tid = row["id"]
        can_work = not row["is_completed"] and not row["is_dumped"] and not row["in_work"]
        can_dump = not row["is_dumped"] and not row["is_completed"]

        if add_btn:
            try:
                add_btn.clicked.disconnect()
            except:
                pass
            add_btn.clicked.connect(lambda _=False, i=tid: self._add_to_work(i))
            add_btn.setVisible(can_work)
        if dump_btn:
            try:
                dump_btn.clicked.disconnect()
            except:
                pass
            dump_btn.clicked.connect(lambda _=False, i=tid: self._move_to_dump(i))
            dump_btn.setVisible(can_dump)

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
        reply = QMessageBox.warning(
            self,
            "Confirm Dump",
            "Are you sure you want to move this task to dump?\nThis action cannot be undone easily.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            task_manager.update_task_fields(
                task_id, is_dumped=True, in_work=False
            )
            self._refresh()

    def _refresh(self):
        self.setUpdatesEnabled(False)
        try:
            self._rebuild_cache()
            self._update_stats()
            self._render_work_table()
            self._render_task_list()
        finally:
            self.setUpdatesEnabled(True)
            self.update()

    def showEvent(self, event):
        super().showEvent(event)
        # Only refresh on first show to avoid flickering when switching sections
        if not getattr(self, "_has_shown_once", False):
            self._has_shown_once = True
            self._refresh()
