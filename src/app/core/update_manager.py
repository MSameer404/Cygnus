# src/app/core/update_manager.py
"""Auto-update system: checks GitHub releases, downloads, and installs updates."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QThread, pyqtSignal


def get_current_version() -> str:
    """Read version from pyproject.toml."""
    try:
        pyproject_path = Path(__file__).parent.parent.parent.parent / "pyproject.toml"
        with open(pyproject_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("version"):
                    # Extract version from version = "x.x.x"
                    parts = line.split("=")
                    if len(parts) >= 2:
                        version = parts[1].strip().strip('"').strip("'")
                        return version
    except Exception:
        pass
    return "1.0.0"


CURRENT_VERSION = get_current_version()
GITHUB_API_URL = "https://api.github.com/repos/MohammadSameer-Dev/Cygnus/releases/latest"


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
            # Fallback to string comparison if parsing fails
            return remote != current


def pick_windows_asset(assets: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Select Windows installer asset from release assets.
    
    Looks for asset with:
    - Filename ends with .exe
    - Filename contains 'windows' (case-insensitive)
    """
    for asset in assets:
        name = asset.get("name", "").lower()
        if name.endswith(".exe") and "windows" in name:
            return asset
    return None


class DownloadWorker(QThread):
    """Worker thread to download update file with progress reporting."""

    progress = pyqtSignal(int)  # 0-100 percent
    finished = pyqtSignal(str)  # filepath
    error = pyqtSignal(str)

    def __init__(self, download_url: str, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self._temp_path = None

    def run(self):
        """Download file to temporary location."""
        try:
            # Create temp file with .exe extension
            fd, temp_path = tempfile.mkstemp(suffix=".exe", prefix="cygnus_update_")
            os.close(fd)
            self._temp_path = temp_path

            req = urllib.request.Request(
                self.download_url,
                headers={"User-Agent": f"Cygnus/{CURRENT_VERSION}"},
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 8192

                with open(temp_path, "wb") as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            self.progress.emit(percent)

            self.finished.emit(temp_path)

        except Exception as e:
            # Clean up temp file on error
            if self._temp_path and os.path.exists(self._temp_path):
                try:
                    os.remove(self._temp_path)
                except OSError:
                    pass
            self.error.emit(f"Download failed: {str(e)}")


class UpdateManager:
    """Manages the update check and download process."""

    _instance: UpdateManager | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._check_worker: CheckUpdateWorker | None = None
            cls._instance._download_worker: DownloadWorker | None = None
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
        result = dialog.exec()

        if result == UpdateDialog.DialogCode.Accepted:
            asset = pick_windows_asset(assets)
            if asset:
                self._start_download(asset["browser_download_url"], parent_widget)
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    parent_widget,
                    "No Windows Installer",
                    "Could not find a Windows installer in this release.",
                )

    def _start_download(self, download_url: str, parent_widget):
        """Start downloading the update."""
        from PyQt6.QtWidgets import QMessageBox, QProgressDialog

        # Create progress dialog
        progress = QProgressDialog("Downloading update...", "Cancel", 0, 100, parent_widget)
        progress.setWindowTitle("Downloading Update")
        progress.setModal(True)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        self._download_worker = DownloadWorker(download_url)
        self._download_worker.progress.connect(progress.setValue)
        self._download_worker.finished.connect(
            lambda path: self._on_download_finished(path, progress)
        )
        self._download_worker.error.connect(
            lambda msg: self._on_download_error(msg, progress, parent_widget)
        )
        progress.canceled.connect(self._download_worker.terminate)
        
        self._download_worker.finished.connect(self._cleanup_download_worker)
        self._download_worker.error.connect(self._cleanup_download_worker)

        self._download_worker.start()

    def _on_download_finished(self, filepath: str, progress_dialog):
        """Handle successful download - launch installer and exit."""
        from PyQt6.QtWidgets import QMessageBox

        progress_dialog.close()

        reply = QMessageBox.question(
            None,
            "Install Update",
            "Download complete. The installer will now run and the app will close.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Launch installer on Windows
                if platform.system() == "Windows":
                    subprocess.Popen([filepath], shell=True)
                else:
                    # Fallback - just open the file
                    os.startfile(filepath)
            except Exception as e:
                QMessageBox.warning(
                    None, "Launch Failed", f"Could not launch installer: {str(e)}"
                )
                return
            
            # Exit the application
            sys.exit(0)

    def _on_download_error(self, message: str, progress_dialog, parent_widget):
        """Handle download error."""
        from PyQt6.QtWidgets import QMessageBox

        progress_dialog.close()
        QMessageBox.warning(parent_widget, "Download Failed", message)

    def _cleanup_download_worker(self):
        """Clean up download worker after completion."""
        self._download_worker = None


# Singleton accessor
def get_update_manager() -> UpdateManager:
    """Get the singleton UpdateManager instance."""
    return UpdateManager()
