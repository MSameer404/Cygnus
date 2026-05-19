from pathlib import Path

def get_assets_dir():
    """
    Returns the path to the assets directory.
    """
    # This file is in src/app/core/utils.py
    # Assets are in src/app/assets
    return Path(__file__).parent.parent / "assets"

def get_asset_path(filename):
    """Returns the full path to a specific asset file."""
    return get_assets_dir() / filename

def get_icon_path(filename):
    """Returns the full path to a specific icon file."""
    return get_assets_dir() / "icons" / filename


def get_current_version() -> str:
    """Read version from package metadata or pyproject.toml."""
    from importlib.metadata import version, PackageNotFoundError

    # Try package metadata first (if installed via pip/uv)
    try:
        return version("cygnus")
    except PackageNotFoundError:
        pass

    # Try to read from pyproject.toml (in-tree running/development)
    try:
        pyproject_path = Path(__file__).parent.parent.parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("version"):
                        parts = line.split("=")
                        if len(parts) >= 2:
                            return parts[1].strip().strip('"').strip("'")
    except Exception:
        pass

    # Hardcoded fallback version
    return "2.3.0"


CURRENT_VERSION = get_current_version()
