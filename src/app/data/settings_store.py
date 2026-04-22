# src/app/data/settings_store.py
"""Simple JSON-based settings storage for user preferences."""

import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent / "user_settings.json"


def load_setting(key: str, default=None):
    """Load a setting value."""
    try:
        if SETTINGS_FILE.exists():
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            return data.get(key, default)
    except Exception:
        pass
    return default


def save_setting(key: str, value):
    """Save a setting value."""
    try:
        data = {}
        if SETTINGS_FILE.exists():
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        data[key] = value
        SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass
