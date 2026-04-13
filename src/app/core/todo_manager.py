# src/app/core/todo_manager.py
"""CRUD operations for to-do items."""

from datetime import date

from sqlmodel import and_, select, func

from app.data.database import get_session
from app.data.models import TodoItem


def create_todo(
    title: str,
    target_date: date | None = None,
    subject_id: int | None = None,
) -> TodoItem:
    """Create a new to-do item."""
    with get_session() as session:
        todo = TodoItem(
            title=title.strip(),
            target_date=target_date or date.today(),
            subject_id=subject_id,
        )
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo


def list_todos(
    target_date: date | None = None,
    completed: bool | None = None,
) -> list[TodoItem]:
    """List to-do items, optionally filtered by date and completion status."""
    with get_session() as session:
        stmt = select(TodoItem)

        if target_date is not None:
            stmt = stmt.where(TodoItem.target_date == target_date)
        if completed is not None:
            stmt = stmt.where(TodoItem.is_completed == completed)

        stmt = stmt.order_by(TodoItem.is_completed, TodoItem.created_at.desc())
        return list(session.exec(stmt).all())


def toggle_todo(todo_id: int) -> TodoItem | None:
    """Toggle a to-do item's completion status."""
    with get_session() as session:
        todo = session.get(TodoItem, todo_id)
        if todo is None:
            return None
        todo.is_completed = not todo.is_completed
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo


def update_todo(todo_id: int, title: str | None = None, subject_id: int | None = -1) -> TodoItem | None:
    """Update a to-do item."""
    with get_session() as session:
        todo = session.get(TodoItem, todo_id)
        if todo is None:
            return None
        if title is not None:
            todo.title = title.strip()
        if subject_id != -1:  # -1 means "don't change"
            todo.subject_id = subject_id
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo


def delete_todo(todo_id: int) -> bool:
    """Delete a to-do item."""
    with get_session() as session:
        todo = session.get(TodoItem, todo_id)
        if todo is None:
            return False
        session.delete(todo)
        session.commit()
        return True


def get_completion_rate(target_date: date) -> float:
    """Return completion percentage for a given date (0.0 to 100.0)."""
    with get_session() as session:
        total = session.exec(
            select(func.count(TodoItem.id)).where(TodoItem.target_date == target_date)
        ).one()
        if total == 0:
            return 0.0
        completed = session.exec(
            select(func.count(TodoItem.id)).where(
                and_(
                    TodoItem.target_date == target_date,
                    TodoItem.is_completed == True,
                )
            )
        ).one()
        return (completed / total) * 100


def get_pending_count(target_date: date | None = None) -> int:
    """Return count of pending (incomplete) todos."""
    with get_session() as session:
        stmt = select(func.count(TodoItem.id)).where(TodoItem.is_completed == False)
        if target_date:
            stmt = stmt.where(TodoItem.target_date == target_date)
        return session.exec(stmt).one()
