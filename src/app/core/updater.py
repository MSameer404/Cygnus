import os
import sys
import requests
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox

GITHUB_REPO = "MSameer404/Cygnus"
CURRENT_VERSION = "2.3.0"

class AutoUpdater:
    def __init__(self, current_version=CURRENT_VERSION):
        self.current_version = current_version
        self.latest_release_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

    def check_for_updates(self, silent=True):
        """
        Checks GitHub for a newer version.
        If silent=True, it only shows a message if an update is found.
        """
        try:
            response = requests.get(self.latest_release_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            latest_version = data["tag_name"].lstrip("v")
            
            if self._is_newer(latest_version, self.current_version):
                return data # Return release data if update found
            
            return None
        except Exception as e:
            print(f"Update check failed: {e}")
            return None

    def _is_newer(self, latest, current):
        # Simple semantic version comparison
        try:
            l_parts = [int(p) for p in latest.split(".")]
            c_parts = [int(p) for p in current.split(".")]
            return l_parts > c_parts
        except (ValueError, AttributeError):
            return latest != current

    def download_and_install(self, release_data, parent_window=None):
        """
        Downloads the installer from the release and runs it.
        """
        # Find the setup.exe in assets
        installer_url = None
        for asset in release_data.get("assets", []):
            if asset["name"].endswith("_Setup.exe") or asset["name"] == "Cygnus_Setup.exe":
                installer_url = asset["browser_download_url"]
                break
        
        if not installer_url:
            if parent_window:
                QMessageBox.warning(parent_window, "Update Error", "No installer found in the latest release.")
            return False

        # Download path
        temp_dir = Path(os.environ.get("TEMP", "."))
        download_path = temp_dir / "Cygnus_Setup.exe"

        try:
            if parent_window:
                reply = QMessageBox.question(
                    parent_window, 
                    "Update Available", 
                    f"A new version ({release_data['tag_name']}) is available. Download and install now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return False

            # Download the file
            response = requests.get(installer_url, stream=True)
            response.raise_for_status()
            
            with open(download_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Run the installer and exit
            subprocess.Popen([str(download_path), "/SILENT"], shell=True)
            sys.exit(0)
            
        except Exception as e:
            if parent_window:
                QMessageBox.critical(parent_window, "Download Error", f"Failed to download update: {e}")
            return False
