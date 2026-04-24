# src/app/core/update_manager.py
"""Simple update checker: checks GitHub releases and shows download link."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QThread, pyqtSignal


def get_current_version() -> str:
    """Read version from pyproject.toml or bundled resources."""
    # Try to read from pyproject.toml (development mode)
    try:
        pyproject_path = Path(__file__).parent.parent.parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("version"):
                        parts = line.split("=")
                        if len(parts) >= 2:
                            version = parts[1].strip().strip('"').strip("'")
                            return version
    except Exception:
        pass
    
    # Try to read from bundled version file (PyInstaller mode)
    try:
        # In PyInstaller, files are extracted to a temp folder
        bundle_dir = Path(getattr(sys, '_MEIPASS', Path(__file__).parent.parent.parent.parent))
        version_path = bundle_dir / "version.txt"
        if version_path.exists():
            return version_path.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    
    # Hardcoded fallback version (must be updated manually for each release)
    return "2.2.0"


CURRENT_VERSION = get_current_version()
GITHUB_API_URL = "https://api.github.com/repos/MohammadSameer-Dev/Cygnus/releases/latest"
GITHUB_RELEASES_URL = "https://github.com/MohammadSameer-Dev/Cygnus/releases/latest"


class CheckUpdateWorker(QThread):
    """Worker thread to check for updates from GitHub releases."""

    update_available = pyqtSignal(str, str, list)  # version, changelog, assets
    no_update = pyqtSignal()
    error = pyqtSignal(str)

    def run(self):
        """Fetch latest release from GitHub API."""
        try:
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={
                    "User-Agent": f"Cygnus/{CURRENT_VERSION}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            latest_version = data.get("tag_name", "").lstrip("v")
            changelog = data.get("body", "No changelog available.")
            assets = data.get("assets", [])

            if not latest_version:
                self.error.emit("Could not parse version from GitHub release.")
                return

            if self._is_newer_version(latest_version, CURRENT_VERSION):
                self.update_available.emit(latest_version, changelog, assets)
            else:
                self.no_update.emit()

        except urllib.error.HTTPError as e:
            self.error.emit(f"GitHub API error: {e.code} {e.reason}")
        except urllib.error.URLError as e:
            self.error.emit(f"Network error: {e.reason}")
        except json.JSONDecodeError:
            self.error.emit("Failed to parse GitHub response.")
        except Exception as e:
            self.error.emit(f"Unexpected error: {str(e)}")

    @staticmethod
    def _is_newer_version(remote: str, current: str) -> bool:
        """Compare version strings. Returns True if remote is newer."""
        try:
            remote_parts = tuple(int(x) for x in remote.split(".") if x.isdigit())
            current_parts = tuple(int(x) for x in current.split(".") if x.isdigit())
            return remote_parts > current_parts
        except (ValueError, AttributeError):
            return remote != current


def pick_windows_asset(assets: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Select Windows installer asset from release assets."""
    for asset in assets:
        name = asset.get("name", "").lower()
        if name.endswith(".exe") and "windows" in name:
            return asset
    return None


class UpdateManager:
    """Manages the update check process - only shows info, no auto-download."""

    _instance: UpdateManager | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._check_worker: CheckUpdateWorker | None = None
        return cls._instance

    def check_for_update(self, parent_widget) -> CheckUpdateWorker:
        """Start checking for updates. Returns the worker thread."""
        from PyQt6.QtWidgets import QMessageBox

        self._check_worker = CheckUpdateWorker()

        self._check_worker.update_available.connect(
            lambda version, changelog, assets: self._on_update_available(
                parent_widget, version, changelog, assets
            )
        )
        self._check_worker.no_update.connect(
            lambda: QMessageBox.information(
                parent_widget,
                "No Update Available",
                f"You are running the latest version ({CURRENT_VERSION}).",
            )
        )
        self._check_worker.error.connect(
            lambda msg: QMessageBox.warning(parent_widget, "Update Check Failed", msg)
        )
        self._check_worker.finished.connect(self._cleanup_check_worker)

        self._check_worker.start()
        return self._check_worker

    def _cleanup_check_worker(self):
        """Clean up check worker after completion."""
        self._check_worker = None

    def _on_update_available(
        self, parent_widget, version: str, changelog: str, assets: list
    ):
        """Show update dialog when an update is available."""
        from app.ui.widgets.update_dialog import UpdateDialog

        dialog = UpdateDialog(version, changelog, assets, parent=parent_widget)
        dialog.exec()


def get_update_manager() -> UpdateManager:
    """Get the singleton UpdateManager instance."""
    return UpdateManager()
