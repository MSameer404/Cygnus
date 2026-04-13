# src/app/core/dday_manager.py
"""CRUD operations for D-Day countdown events."""

from datetime import date

from sqlmodel import select

from app.data.database import get_session
from app.data.models import DDayEvent


def list_events() -> list[DDayEvent]:
    """Return all D-Day events ordered by target date."""
    with get_session() as session:
        stmt = select(DDayEvent).order_by(DDayEvent.target_date)
        return list(session.exec(stmt).all())


def list_upcoming_events() -> list[DDayEvent]:
    """Return D-Day events that haven't passed yet."""
    with get_session() as session:
        stmt = (
            select(DDayEvent)
            .where(DDayEvent.target_date >= date.today())
            .order_by(DDayEvent.target_date)
        )
        return list(session.exec(stmt).all())


def create_event(title: str, target_date: date, color_hex: str = "#FDCB6E") -> DDayEvent:
    """Create a new D-Day event."""
    with get_session() as session:
        event = DDayEvent(title=title.strip(), target_date=target_date, color_hex=color_hex)
        session.add(event)
        session.commit()
        session.refresh(event)
        return event


def get_days_remaining(event: DDayEvent) -> int:
    """Return days until the event (negative if past)."""
    return (event.target_date - date.today()).days


def delete_event(event_id: int) -> bool:
    """Delete a D-Day event."""
    with get_session() as session:
        event = session.get(DDayEvent, event_id)
        if event is None:
            return False
        session.delete(event)
        session.commit()
        return True
