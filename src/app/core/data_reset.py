# src/app/core/data_reset.py
"""Complete data reset functionality - deletes database and profile picture."""

import os
from pathlib import Path

from app.data.database import DATA_DIR, DB_PATH, close_engine, reinit_engine, init_db
from app.core.profile_manager import PROFILE_PICTURE_PATH


def reset_all_data() -> None:
    """
    Reset all app data to factory defaults.

    This will:
    1. Close the database engine to release file locks
    2. Delete the SQLite database file (all sessions, tasks, events, settings)
    3. Delete the profile picture
    4. Recreate the engine and reinitialize with default data
    """
    # Step 1: Close engine to release file lock
    close_engine()

    # Step 2: Delete profile picture if exists
    if PROFILE_PICTURE_PATH.exists():
        PROFILE_PICTURE_PATH.unlink()

    # Step 3: Delete database file if exists
    if DB_PATH.exists():
        os.remove(DB_PATH)

    # Step 4: Recreate engine and reinitialize database
    reinit_engine()
    init_db()


def get_data_directory() -> Path:
    """Return the path to the app's data directory."""
    return DATA_DIR
