# src/app/data/models.py
"""SQLModel table definitions for Cygnus."""

from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel

# Priority ordering helper (used for sorting chapters)
PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


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


class TaskItem(SQLModel, table=True):
    """A task optionally linked to a subject."""

    __tablename__ = "todo_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    subject_id: Optional[int] = Field(default=None, foreign_key="subjects.id")
    title: str
    is_completed: bool = Field(default=False)
    target_date: date = Field(default_factory=date.today)
    created_at: datetime = Field(default_factory=datetime.now)
    priority: str = Field(default="med")  # high | med | low
    in_work: bool = Field(default=False)
    is_dumped: bool = Field(default=False)


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


# ──────────────────────────────────────────────
# Syllabus Tracker tables
# ──────────────────────────────────────────────

class SyllabusChapter(SQLModel, table=True):
    """One chapter row inside a subject's syllabus table."""

    __tablename__ = "syllabus_chapters"

    id: Optional[int] = Field(default=None, primary_key=True)
    subject_id: int = Field(foreign_key="subjects.id", index=True)
    name: str = Field(default="")
    priority: str = Field(default="Medium")  # High | Medium | Low
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)


class SyllabusMaterial(SQLModel, table=True):
    """A material column definition for a subject (max 4 per subject)."""

    __tablename__ = "syllabus_materials"

    id: Optional[int] = Field(default=None, primary_key=True)
    subject_id: int = Field(foreign_key="subjects.id", index=True)
    name: str = Field(default="Material")
    col_index: int = Field(default=0)  # 0-3
    created_at: datetime = Field(default_factory=datetime.now)


class SyllabusProgress(SQLModel, table=True):
    """Checkbox state for a (chapter, material) pair."""

    __tablename__ = "syllabus_progress"

    id: Optional[int] = Field(default=None, primary_key=True)
    chapter_id: int = Field(foreign_key="syllabus_chapters.id", index=True)
    material_id: int = Field(foreign_key="syllabus_materials.id", index=True)
    is_done: bool = Field(default=False)
