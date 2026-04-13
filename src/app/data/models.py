# src/app/data/models.py
"""SQLModel table definitions for Cygnus."""

from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Subject(SQLModel, table=True):
    """A study subject (e.g., Physics, Chemistry, Math)."""

    __tablename__ = "subjects"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    color_hex: str = Field(default="#6C5CE7")
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)


class StudySession(SQLModel, table=True):
    """A single study session with start/end time and subject."""

    __tablename__ = "study_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    subject_id: int = Field(foreign_key="subjects.id", index=True)
    start_time: datetime
    end_time: datetime
    duration_seconds: int = Field(default=0)
    notes: str = Field(default="")


class TodoItem(SQLModel, table=True):
    """A to-do item optionally linked to a subject."""

    __tablename__ = "todo_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    subject_id: Optional[int] = Field(default=None, foreign_key="subjects.id")
    title: str
    is_completed: bool = Field(default=False)
    target_date: date = Field(default_factory=date.today)
    created_at: datetime = Field(default_factory=datetime.now)


class DDayEvent(SQLModel, table=True):
    """A countdown event (exam, deadline, etc.)."""

    __tablename__ = "dday_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    target_date: date
    color_hex: str = Field(default="#FDCB6E")
    created_at: datetime = Field(default_factory=datetime.now)


class AppSetting(SQLModel, table=True):
    """Key-value store for app settings."""

    __tablename__ = "app_settings"

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True)
    value: str = Field(default="")
