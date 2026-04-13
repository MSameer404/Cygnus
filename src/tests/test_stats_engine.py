# src/tests/test_stats_engine.py
"""Tests for stats_engine aggregation functions."""

from datetime import date, datetime

import pytest

from app.core import session_manager, stats_engine
from app.data.database import init_db


@pytest.fixture(autouse=True)
def setup_db(test_db):
    init_db()


def _add_session(day: date, hours: float):
    """Helper to add a session for a given day."""
    start = datetime(day.year, day.month, day.day, 9, 0)
    secs = int(hours * 3600)
    end = datetime(day.year, day.month, day.day, 9 + int(hours), int((hours % 1) * 60))
    session_manager.save_session(1, start, end, secs)


def test_daily_total():
    d = date(2026, 3, 1)
    _add_session(d, 2)
    _add_session(d, 1.5)

    total = stats_engine.get_daily_total(d)
    assert total == int(3.5 * 3600)


def test_weekly_totals():
    # Week starting Monday 2026-03-02
    start = date(2026, 3, 2)
    _add_session(start, 2)  # Mon
    _add_session(date(2026, 3, 4), 3)  # Wed

    totals = stats_engine.get_weekly_totals(start)
    assert len(totals) == 7
    assert totals[0] == 2 * 3600  # Mon
    assert totals[2] == 3 * 3600  # Wed
    assert totals[1] == 0  # Tue


def test_subject_breakdown():
    d = date(2026, 3, 1)
    session_manager.save_session(1, datetime(2026, 3, 1, 9, 0), datetime(2026, 3, 1, 10, 0), 3600)
    session_manager.save_session(2, datetime(2026, 3, 1, 10, 0), datetime(2026, 3, 1, 11, 0), 3600)

    breakdown = stats_engine.get_subject_breakdown(d, d)
    assert len(breakdown) == 2
    total_secs = sum(v["seconds"] for v in breakdown.values())
    assert total_secs == 7200


def test_streak():
    today = date.today()
    # No sessions = 0 streak
    assert stats_engine.get_streak() == 0

    # Add today
    _add_session(today, 1)
    assert stats_engine.get_streak() == 1


def test_average_daily():
    d1 = date(2026, 3, 1)
    d2 = date(2026, 3, 2)
    _add_session(d1, 4)
    _add_session(d2, 2)

    avg = stats_engine.get_average_daily(d1, d2)
    assert avg == int(3 * 3600)  # (4+2)/2 = 3 hours avg


def test_best_day():
    d1 = date(2026, 3, 1)
    d2 = date(2026, 3, 2)
    _add_session(d1, 2)
    _add_session(d2, 5)

    best_date, best_secs = stats_engine.get_best_day(d1, d2)
    assert best_date == d2
    assert best_secs == 5 * 3600
