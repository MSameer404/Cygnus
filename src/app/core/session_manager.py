# src/app/core/session_manager.py
"""CRUD operations for study sessions with overlap detection."""

from datetime import date, datetime, time

from sqlmodel import and_, select

from app.data.database import get_session
from app.data.models import StudySession


def save_session(
    subject_id: int,
    start_time: datetime,
    end_time: datetime,
    duration_seconds: int,
    notes: str = "",
) -> StudySession:
    """Save a completed study session to the database."""
    with get_session() as session:
        study = StudySession(
            subject_id=subject_id,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration_seconds,
            notes=notes,
        )
        session.add(study)
        session.commit()
        session.refresh(study)
        return study


def add_manual_session(
    subject_id: int,
    session_date: date,
    start_time: time,
    end_time: time,
    notes: str = "",
) -> StudySession:
    """Manually add a past session. Validates no overlaps."""
    start_dt = datetime.combine(session_date, start_time)
    end_dt = datetime.combine(session_date, end_time)

    if end_dt <= start_dt:
        raise ValueError("End time must be after start time.")

    duration = int((end_dt - start_dt).total_seconds())

    # Check for overlaps
    if has_overlap(start_dt, end_dt):
        raise ValueError("This session overlaps with an existing session.")

    return save_session(subject_id, start_dt, end_dt, duration, notes)


def has_overlap(start_dt: datetime, end_dt: datetime, exclude_id: int | None = None) -> bool:
    """Check if a time range overlaps with any existing session."""
    with get_session() as session:
        stmt = select(StudySession).where(
            and_(
                StudySession.start_time < end_dt,
                StudySession.end_time > start_dt,
            )
        )
        if exclude_id is not None:
            stmt = stmt.where(StudySession.id != exclude_id)

        return session.exec(stmt).first() is not None


def get_sessions_for_date(target_date: date) -> list[StudySession]:
    """Get all sessions for a specific date, ordered by start time."""
    day_start = datetime.combine(target_date, time.min)
    day_end = datetime.combine(target_date, time.max)

    with get_session() as session:
        stmt = (
            select(StudySession)
            .where(
                and_(
                    StudySession.start_time >= day_start,
                    StudySession.start_time <= day_end,
                )
            )
            .order_by(StudySession.start_time)
        )
        return list(session.exec(stmt).all())


def get_sessions_for_range(start_date: date, end_date: date) -> list[StudySession]:
    """Get all sessions within a date range (inclusive)."""
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)

    with get_session() as session:
        stmt = (
            select(StudySession)
            .where(
                and_(
                    StudySession.start_time >= start_dt,
                    StudySession.start_time <= end_dt,
                )
            )
            .order_by(StudySession.start_time)
        )
        return list(session.exec(stmt).all())


def get_total_seconds_for_date(target_date: date) -> int:
    """Get total study seconds for a given date."""
    sessions = get_sessions_for_date(target_date)
    return sum(s.duration_seconds for s in sessions)


def delete_session(session_id: int) -> bool:
    """Delete a session by ID. Returns True if deleted."""
    with get_session() as session:
        study = session.get(StudySession, session_id)
        if study is None:
            return False
        session.delete(study)
        session.commit()
        return True
