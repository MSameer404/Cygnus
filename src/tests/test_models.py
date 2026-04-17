# src/tests/test_models.py
"""Tests for SQLModel table definitions."""

import pytest
from datetime import date, datetime

from app.data.database import init_db, get_session
from app.data.models import Subject, StudySession, TaskItem, DDayEvent, AppSetting
from app.core import task_manager


@pytest.fixture(autouse=True)
def setup_db(test_db):
    init_db()


def test_default_subjects_seeded():
    with get_session() as session:
        from sqlmodel import select
        subjects = list(session.exec(select(Subject)).all())
        assert len(subjects) == 3
        names = {s.name for s in subjects}
        assert "Physics" in names
        assert "Chemistry" in names
        assert "Math" in names


def test_default_settings_seeded():
    with get_session() as session:
        from sqlmodel import select
        settings = list(session.exec(select(AppSetting)).all())
        assert len(settings) >= 1
        keys = {s.key for s in settings}
        assert "day_boundary" in keys


def test_create_study_session():
    with get_session() as session:
        s = StudySession(
            subject_id=1,
            start_time=datetime(2026, 1, 1, 9, 0),
            end_time=datetime(2026, 1, 1, 10, 0),
            duration_seconds=3600,
        )
        session.add(s)
        session.commit()
        session.refresh(s)
        assert s.id is not None


def test_create_task():
    with get_session() as session:
        t = TaskItem(title="Study chapter 5", target_date=date.today())
        session.add(t)
        session.commit()
        session.refresh(t)
        assert t.id is not None
        assert t.is_completed is False
        assert t.priority == "med"
        assert t.in_work is False
        assert t.is_dumped is False


def test_task_manager_create_priority_and_list_all():
    t = task_manager.create_task("Priority task", priority="high")
    assert t.priority == "high"
    all_rows = task_manager.list_all_tasks()
    assert any(r.id == t.id for r in all_rows)


def test_task_manager_update_fields():
    t = task_manager.create_task("W", priority="low")
    u = task_manager.update_task_fields(t.id, in_work=True)
    assert u is not None
    assert u.in_work is True
    u2 = task_manager.update_task_fields(t.id, is_completed=True, in_work=False)
    assert u2 is not None
    assert u2.is_completed is True
    assert u2.in_work is False


def test_create_dday_event():
    with get_session() as session:
        e = DDayEvent(
            title="Final Exam",
            target_date=date(2026, 6, 15),
        )
        session.add(e)
        session.commit()
        session.refresh(e)
        assert e.id is not None
