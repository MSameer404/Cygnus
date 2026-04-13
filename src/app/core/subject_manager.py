# src/app/core/subject_manager.py
"""CRUD operations for study subjects."""

import re

from sqlmodel import select

from app.data.database import get_session
from app.data.models import Subject


def list_subjects() -> list[Subject]:
    """Return all subjects ordered by sort_order."""
    with get_session() as session:
        stmt = select(Subject).order_by(Subject.sort_order)
        return list(session.exec(stmt).all())


def get_subject(subject_id: int) -> Subject | None:
    """Get a subject by ID."""
    with get_session() as session:
        return session.get(Subject, subject_id)


def create_subject(name: str, color_hex: str = "#6C5CE7") -> Subject:
    """Create a new subject with the given name and color."""
    _validate_color(color_hex)
    with get_session() as session:
        # Get next sort order
        existing = session.exec(
            select(Subject).order_by(Subject.sort_order.desc())
        ).first()
        next_order = (existing.sort_order + 1) if existing else 0

        subject = Subject(name=name.strip(), color_hex=color_hex, sort_order=next_order)
        session.add(subject)
        session.commit()
        session.refresh(subject)
        return subject


def update_subject(subject_id: int, name: str | None = None, color_hex: str | None = None) -> Subject | None:
    """Update an existing subject's name and/or color."""
    with get_session() as session:
        subject = session.get(Subject, subject_id)
        if subject is None:
            return None
        if name is not None:
            subject.name = name.strip()
        if color_hex is not None:
            _validate_color(color_hex)
            subject.color_hex = color_hex
        session.add(subject)
        session.commit()
        session.refresh(subject)
        return subject


def delete_subject(subject_id: int) -> bool:
    """Delete a subject. Returns True if deleted."""
    with get_session() as session:
        subject = session.get(Subject, subject_id)
        if subject is None:
            return False
        session.delete(subject)
        session.commit()
        return True


def _validate_color(color_hex: str):
    """Validate that color_hex is a valid hex color."""
    if not re.match(r"^#[0-9A-Fa-f]{6}$", color_hex):
        raise ValueError(f"Invalid hex color: {color_hex}")
