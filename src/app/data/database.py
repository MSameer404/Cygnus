# src/app/data/database.py
"""Database engine, session management, and initialization."""

import os
from contextlib import contextmanager
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine, select

from app.data.models import AppSetting, Subject

# ---------- Database path ----------

_APPDATA = os.environ.get("APPDATA", os.path.expanduser("~"))
DATA_DIR = Path(_APPDATA) / "Cygnus"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "cygnus_data.db"

_engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# ---------- Default data ----------

DEFAULT_SUBJECTS = [
    Subject(name="Physics", color_hex="#6C5CE7", sort_order=0),
    Subject(name="Chemistry", color_hex="#00CEC9", sort_order=1),
    Subject(name="Math", color_hex="#FF6B6B", sort_order=2),
]

DEFAULT_SETTINGS = {
    "day_boundary": "00:00",  # midnight
}


# ---------- Public API ----------


def init_db() -> None:
    """Create all tables and seed default data if first run."""
    SQLModel.metadata.create_all(_engine)

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
