import sys
import os
from pathlib import Path

def get_assets_dir():
    """
    Returns the path to the assets directory, handling both 
    development and PyInstaller frozen states.
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        # PyInstaller extracts to a temp folder stored in sys._MEIPASS
        # Based on build.py: --add-data="src/app/assets;app/assets"
        return Path(sys._MEIPASS) / "app" / "assets"
    else:
        # Running normally
        # This file is in src/app/core/utils.py
        # Assets are in src/app/assets
        return Path(__file__).parent.parent / "assets"

def get_asset_path(filename):
    """Returns the full path to a specific asset file."""
    return get_assets_dir() / filename

def get_icon_path(filename):
    """Returns the full path to a specific icon file."""
    return get_assets_dir() / "icons" / filename
