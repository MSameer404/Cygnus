# src/app/core/profile_manager.py
"""Manage user profile data stored in the app_settings key-value table."""

import shutil
from datetime import date
from pathlib import Path
from typing import Optional

from sqlmodel import select

from app.data.database import DATA_DIR, get_session
from app.data.models import AppSetting

# Profile keys stored as "profile.<field>" in app_settings
PROFILE_FIELDS = {
    "name": "Cygnus",          # default
    "class": "",               # optional
    "target_exam": "",         # optional
    "daily_goal_hours": "6",   # default 6 hours
    "start_date": "",          # optional
    "profile_picture": "",     # path to saved profile picture
}

# Profile picture is stored as a file in the data directory
PROFILE_PICTURE_PATH = DATA_DIR / "profile_picture.png"


def _key(field: str) -> str:
    return f"profile.{field}"


def get_profile() -> dict[str, str]:
    """Return all profile fields as a dict.  Missing keys get defaults."""
    data = dict(PROFILE_FIELDS)  # start with defaults
    with get_session() as session:
        for field in PROFILE_FIELDS:
            row = session.exec(
                select(AppSetting).where(AppSetting.key == _key(field))
            ).first()
            if row is not None:
                data[field] = row.value
    return data


def save_profile(data: dict[str, str]) -> None:
    """Upsert each profile field into app_settings."""
    with get_session() as session:
        for field, value in data.items():
            if field not in PROFILE_FIELDS:
                continue
            row = session.exec(
                select(AppSetting).where(AppSetting.key == _key(field))
            ).first()
            if row is None:
                session.add(AppSetting(key=_key(field), value=value))
            else:
                row.value = value
                session.add(row)
        session.commit()


def get_profile_value(field: str) -> str:
    """Get a single profile field value."""
    with get_session() as session:
        row = session.exec(
            select(AppSetting).where(AppSetting.key == _key(field))
        ).first()
        if row is not None:
            return row.value
    return PROFILE_FIELDS.get(field, "")


def get_display_name() -> str:
    """Return the user's display name (defaults to 'Cygnus')."""
    name = get_profile_value("name")
    return name if name else "Cygnus"


def get_daily_goal_seconds() -> int:
    """Return the daily study goal in seconds."""
    try:
        hours = float(get_profile_value("daily_goal_hours"))
        return int(hours * 3600)
    except (ValueError, TypeError):
        return 6 * 3600  # default 6 hours


def get_profile_picture_path() -> Optional[Path]:
    """Return the path to the saved profile picture, or None if not set."""
    if PROFILE_PICTURE_PATH.exists():
        return PROFILE_PICTURE_PATH
    return None


def save_profile_picture(source_path: str) -> str:
    """Copy the selected image to the Cygnus data dir as profile_picture.png.

    Returns the destination path as a string.
    """
    src = Path(source_path)
    if not src.exists():
        return ""
    shutil.copy2(str(src), str(PROFILE_PICTURE_PATH))
    # Also store the path in app_settings for reference
    save_profile({"profile_picture": str(PROFILE_PICTURE_PATH)})
    return str(PROFILE_PICTURE_PATH)


def remove_profile_picture() -> None:
    """Delete the saved profile picture."""
    if PROFILE_PICTURE_PATH.exists():
        PROFILE_PICTURE_PATH.unlink()
    save_profile({"profile_picture": ""})
