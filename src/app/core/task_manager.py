# src/app/core/task_manager.py
"""CRUD operations for tasks."""

from datetime import date

from sqlmodel import and_, select, func

from app.data.database import get_session
from app.data.models import TaskItem

_VALID_PRIORITY = frozenset({"high", "med", "low"})
_UNSET = object()


def create_task(
    title: str,
    target_date: date | None = None,
    subject_id: int | None = None,
    priority: str = "med",
) -> TaskItem:
    """Create a new task."""
    p = priority if priority in _VALID_PRIORITY else "med"
    with get_session() as session:
        task = TaskItem(
            title=title.strip(),
            target_date=target_date or date.today(),
            subject_id=subject_id,
            priority=p,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return task


def list_tasks(
    target_date: date | None = None,
    completed: bool | None = None,
    exclude_dumped: bool = True,
) -> list[TaskItem]:
    """List tasks, optionally filtered by date and completion status."""
    with get_session() as session:
        stmt = select(TaskItem)

        if target_date is not None:
            stmt = stmt.where(TaskItem.target_date == target_date)
        if completed is not None:
            stmt = stmt.where(TaskItem.is_completed == completed)
        if exclude_dumped:
            stmt = stmt.where(TaskItem.is_dumped.is_(False))

        stmt = stmt.order_by(TaskItem.is_completed, TaskItem.created_at.desc())
        return list(session.exec(stmt).all())


def list_all_tasks() -> list[TaskItem]:
    """List all tasks (for dashboard aggregates and task list)."""
    with get_session() as session:
        stmt = select(TaskItem).order_by(TaskItem.created_at.desc())
        return list(session.exec(stmt).all())


def toggle_task(task_id: int) -> TaskItem | None:
    """Toggle a task's completion status."""
    with get_session() as session:
        task = session.get(TaskItem, task_id)
        if task is None:
            return None
        task.is_completed = not task.is_completed
        session.add(task)
        session.commit()
        session.refresh(task)
        return task


def update_task(task_id: int, title: str | None = None, subject_id: int | None = -1) -> TaskItem | None:
    """Update a task."""
    with get_session() as session:
        task = session.get(TaskItem, task_id)
        if task is None:
            return None
        if title is not None:
            task.title = title.strip()
        if subject_id != -1:  # -1 means "don't change"
            task.subject_id = subject_id
        session.add(task)
        session.commit()
        session.refresh(task)
        return task


def update_task_fields(
    task_id: int,
    *,
    title: str | object = _UNSET,
    subject_id: int | None | object = _UNSET,
    target_date: date | object = _UNSET,
    priority: str | object = _UNSET,
    is_completed: bool | object = _UNSET,
    in_work: bool | object = _UNSET,
    is_dumped: bool | object = _UNSET,
) -> TaskItem | None:
    """Update allowed fields on a task. Omit a keyword to leave that field unchanged."""
    with get_session() as session:
        task = session.get(TaskItem, task_id)
        if task is None:
            return None
        if title is not _UNSET:
            task.title = str(title).strip()
        if subject_id is not _UNSET:
            task.subject_id = subject_id  # type: ignore[assignment]
        if target_date is not _UNSET:
            task.target_date = target_date  # type: ignore[assignment]
        if priority is not _UNSET and priority in _VALID_PRIORITY:
            task.priority = priority  # type: ignore[assignment]
        if is_completed is not _UNSET:
            task.is_completed = bool(is_completed)
        if in_work is not _UNSET:
            task.in_work = bool(in_work)
        if is_dumped is not _UNSET:
            task.is_dumped = bool(is_dumped)
        session.add(task)
        session.commit()
        session.refresh(task)
        return task


def delete_task(task_id: int) -> bool:
    """Delete a task."""
    with get_session() as session:
        task = session.get(TaskItem, task_id)
        if task is None:
            return False
        session.delete(task)
        session.commit()
        return True


def get_completion_rate(target_date: date) -> float:
    """Return completion percentage for a given date (0.0 to 100.0)."""
    with get_session() as session:
        total = session.exec(
            select(func.count(TaskItem.id)).where(TaskItem.target_date == target_date)
        ).one()
        if total == 0:
            return 0.0
        completed = session.exec(
            select(func.count(TaskItem.id)).where(
                and_(
                    TaskItem.target_date == target_date,
                    TaskItem.is_completed.is_(True),
                )
            )
        ).one()
        return (completed / total) * 100


def list_tasks_for_range(
    start_date: date,
    end_date: date,
) -> list[TaskItem]:
    """List all tasks within a date range (inclusive)."""
    with get_session() as session:
        stmt = (
            select(TaskItem)
            .where(
                and_(
                    TaskItem.target_date >= start_date,
                    TaskItem.target_date <= end_date,
                )
            )
            .order_by(TaskItem.target_date, TaskItem.is_completed, TaskItem.created_at.desc())
        )
        return list(session.exec(stmt).all())


def get_completion_rate_range(start_date: date, end_date: date) -> float:
    """Return completion percentage for a date range (0.0 to 100.0)."""
    with get_session() as session:
        total = session.exec(
            select(func.count(TaskItem.id)).where(
                and_(
                    TaskItem.target_date >= start_date,
                    TaskItem.target_date <= end_date,
                )
            )
        ).one()
        if total == 0:
            return 0.0
        completed = session.exec(
            select(func.count(TaskItem.id)).where(
                and_(
                    TaskItem.target_date >= start_date,
                    TaskItem.target_date <= end_date,
                    TaskItem.is_completed.is_(True),
                )
            )
        ).one()
        return (completed / total) * 100


def get_pending_count(target_date: date | None = None) -> int:
    """Return count of pending (incomplete) tasks."""
    with get_session() as session:
        stmt = select(func.count(TaskItem.id)).where(TaskItem.is_completed.is_(False))
        if target_date:
            stmt = stmt.where(TaskItem.target_date == target_date)
        return session.exec(stmt).one()
