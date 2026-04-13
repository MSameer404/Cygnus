# src/app/core/stats_engine.py
"""Aggregation engine for study statistics and chart data."""

import calendar
from datetime import date, datetime, time, timedelta

from sqlmodel import and_, func, select

from app.data.database import get_session
from app.data.models import StudySession, Subject


def get_daily_total(target_date: date) -> int:
    """Total study seconds for a given date."""
    day_start = datetime.combine(target_date, time.min)
    day_end = datetime.combine(target_date, time.max)

    with get_session() as session:
        result = session.exec(
            select(func.coalesce(func.sum(StudySession.duration_seconds), 0)).where(
                and_(
                    StudySession.start_time >= day_start,
                    StudySession.start_time <= day_end,
                )
            )
        ).one()
        return int(result)


def get_weekly_totals(week_start: date) -> list[int]:
    """Return 7 daily totals (Mon–Sun) for the week starting at week_start."""
    totals = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        totals.append(get_daily_total(d))
    return totals


def get_monthly_totals(year: int, month: int) -> list[int]:
    """Return daily totals for every day in the given month."""
    num_days = calendar.monthrange(year, month)[1]
    totals = []
    for day in range(1, num_days + 1):
        d = date(year, month, day)
        totals.append(get_daily_total(d))
    return totals


def get_subject_breakdown(start_date: date, end_date: date) -> dict[str, dict]:
    """Return {subject_name: {seconds, color_hex}} for the date range."""
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)

    with get_session() as session:
        sessions = session.exec(
            select(StudySession).where(
                and_(
                    StudySession.start_time >= start_dt,
                    StudySession.start_time <= end_dt,
                )
            )
        ).all()

        breakdown = {}
        for s in sessions:
            subj = session.get(Subject, s.subject_id)
            name = subj.name if subj else "Unknown"
            color = subj.color_hex if subj else "#6C5CE7"
            if name not in breakdown:
                breakdown[name] = {"seconds": 0, "color_hex": color}
            breakdown[name]["seconds"] += s.duration_seconds

    return breakdown


def get_streak() -> int:
    """Return count of consecutive days with study sessions ending today."""
    streak = 0
    current = date.today()

    while True:
        total = get_daily_total(current)
        if total > 0:
            streak += 1
            current -= timedelta(days=1)
        else:
            break

    return streak


def get_total_for_range(start_date: date, end_date: date) -> int:
    """Total seconds across a date range."""
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)

    with get_session() as session:
        result = session.exec(
            select(func.coalesce(func.sum(StudySession.duration_seconds), 0)).where(
                and_(
                    StudySession.start_time >= start_dt,
                    StudySession.start_time <= end_dt,
                )
            )
        ).one()
        return int(result)


def get_average_daily(start_date: date, end_date: date) -> int:
    """Average seconds per day for a range."""
    days = (end_date - start_date).days + 1
    if days <= 0:
        return 0
    total = get_total_for_range(start_date, end_date)
    return total // days


def get_best_day(start_date: date, end_date: date) -> tuple[date | None, int]:
    """Return (date, seconds) of the best study day in the range."""
    best_date = None
    best_seconds = 0

    current = start_date
    while current <= end_date:
        total = get_daily_total(current)
        if total > best_seconds:
            best_seconds = total
            best_date = current
        current += timedelta(days=1)

    return best_date, best_seconds


def get_heatmap_data(year: int) -> dict[date, int]:
    """Return {date: seconds} for every day in the given year."""
    start = date(year, 1, 1)
    end = date(year, 12, 31)

    data = {}
    current = start
    while current <= end:
        total = get_daily_total(current)
        if total > 0:
            data[current] = total
        current += timedelta(days=1)

    return data


def get_week_start(d: date) -> date:
    """Return the Monday of the week containing d."""
    return d - timedelta(days=d.weekday())
