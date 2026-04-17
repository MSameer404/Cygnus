# src/app/data/database.py
"""Database engine, session management, and initialization."""

import os
import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine, select

from app.data.models import AppSetting, Subject

# ---------- Database path ----------

_APPDATA = os.environ.get("APPDATA", os.path.expanduser("~"))
DATA_DIR = Path(_APPDATA) / "Cygnus"
DATA_DIR.mkdir(parents=True, exist_ok=True)

if getattr(sys, 'frozen', False):
    DB_PATH = DATA_DIR / "cygnus_data.db"
else:
    DB_PATH = DATA_DIR / "cygnusdev.db"

_engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


def _create_engine():
    """Create a new engine instance."""
    return create_engine(f"sqlite:///{DB_PATH}", echo=False)

# ---------- Default data ----------

DEFAULT_SUBJECTS = [
    Subject(name="Physics", color_hex="#6C5CE7", sort_order=0),
    Subject(name="Chemistry", color_hex="#00CEC9", sort_order=1),
    Subject(name="Math", color_hex="#FF6B6B", sort_order=2),
]

DEFAULT_SETTINGS = {
    "day_boundary": "00:00",  # midnight
}


def _ensure_task_item_columns() -> None:
    """Add new columns to task items on existing SQLite DBs (create_all does not migrate)."""
    if not DB_PATH.exists():
        return
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.execute("PRAGMA table_info(todo_items)")
        cols = {row[1] for row in cur.fetchall()}
        if not cols:
            return
        alters = []
        if "priority" not in cols:
            alters.append(
                "ALTER TABLE todo_items ADD COLUMN priority VARCHAR NOT NULL DEFAULT 'med'"
            )
        if "in_work" not in cols:
            alters.append(
                "ALTER TABLE todo_items ADD COLUMN in_work INTEGER NOT NULL DEFAULT 0"
            )
        if "is_dumped" not in cols:
            alters.append(
                "ALTER TABLE todo_items ADD COLUMN is_dumped INTEGER NOT NULL DEFAULT 0"
            )
        for sql in alters:
            conn.execute(sql)
        conn.commit()
    finally:
        conn.close()


# ---------- Public API ----------


def init_db() -> None:
    """Create all tables and seed default data if first run."""
    SQLModel.metadata.create_all(_engine)
    _ensure_task_item_columns()

    with get_session() as session:
        # Seed subjects if table is empty
        existing = session.exec(select(Subject)).first()
        if existing is None:
            for subj in DEFAULT_SUBJECTS:
                session.add(Subject(
                    name=subj.name,
                    color_hex=subj.color_hex,
                    sort_order=subj.sort_order,
                ))
            session.commit()

        # Seed default settings
        for key, value in DEFAULT_SETTINGS.items():
            existing_setting = session.exec(
                select(AppSetting).where(AppSetting.key == key)
            ).first()
            if existing_setting is None:
                session.add(AppSetting(key=key, value=value))
        session.commit()


@contextmanager
def get_session():
    """Yield a SQLModel Session, auto-closing on exit."""
    session = Session(_engine)
    try:
        yield session
    finally:
        session.close()


def get_engine():
    """Return the SQLAlchemy engine (for advanced use)."""
    return _engine


def close_engine() -> None:
    """Dispose the engine to release database file locks."""
    global _engine
    if _engine:
        _engine.dispose()
        _engine = None


def reinit_engine() -> None:
    """Recreate the engine after database reset."""
    global _engine
    if _engine is None:
        _engine = _create_engine()
