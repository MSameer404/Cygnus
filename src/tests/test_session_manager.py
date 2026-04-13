# src/tests/test_session_manager.py
"""Tests for session_manager CRUD and overlap detection."""

from datetime import date, datetime, time

import pytest

from app.core import session_manager
from app.data.database import init_db


@pytest.fixture(autouse=True)
def setup_db(test_db):
    init_db()


def test_save_session():
    session = session_manager.save_session(
        subject_id=1,
        start_time=datetime(2026, 1, 1, 9, 0),
        end_time=datetime(2026, 1, 1, 10, 0),
        duration_seconds=3600,
    )
    assert session.id is not None
    assert session.duration_seconds == 3600


def test_get_sessions_for_date():
    session_manager.save_session(1, datetime(2026, 1, 1, 9, 0), datetime(2026, 1, 1, 10, 0), 3600)
    session_manager.save_session(1, datetime(2026, 1, 1, 14, 0), datetime(2026, 1, 1, 15, 0), 3600)

    sessions = session_manager.get_sessions_for_date(date(2026, 1, 1))
    assert len(sessions) == 2


def test_get_total_seconds_for_date():
    session_manager.save_session(1, datetime(2026, 1, 1, 9, 0), datetime(2026, 1, 1, 10, 0), 3600)
    session_manager.save_session(1, datetime(2026, 1, 1, 14, 0), datetime(2026, 1, 1, 15, 0), 1800)

    total = session_manager.get_total_seconds_for_date(date(2026, 1, 1))
    assert total == 5400


def test_delete_session():
    session = session_manager.save_session(1, datetime(2026, 1, 1, 9, 0), datetime(2026, 1, 1, 10, 0), 3600)
    assert session_manager.delete_session(session.id) is True
    assert session_manager.get_sessions_for_date(date(2026, 1, 1)) == []


def test_overlap_detection():
    session_manager.save_session(1, datetime(2026, 1, 1, 9, 0), datetime(2026, 1, 1, 10, 0), 3600)

    # Overlapping
    assert session_manager.has_overlap(
        datetime(2026, 1, 1, 9, 30), datetime(2026, 1, 1, 10, 30)
    ) is True

    # Non-overlapping
    assert session_manager.has_overlap(
        datetime(2026, 1, 1, 10, 0), datetime(2026, 1, 1, 11, 0)
    ) is False


def test_manual_session_overlap_raises():
    session_manager.save_session(1, datetime(2026, 1, 1, 9, 0), datetime(2026, 1, 1, 10, 0), 3600)

    with pytest.raises(ValueError, match="overlaps"):
        session_manager.add_manual_session(
            subject_id=1,
            session_date=date(2026, 1, 1),
            start_time=time(9, 30),
            end_time=time(10, 30),
        )


def test_manual_session_end_before_start():
    with pytest.raises(ValueError, match="End time must be after"):
        session_manager.add_manual_session(
            subject_id=1,
            session_date=date(2026, 1, 1),
            start_time=time(10, 0),
            end_time=time(9, 0),
        )
