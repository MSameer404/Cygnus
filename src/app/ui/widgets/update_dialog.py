# src/app/ui/widgets/update_dialog.py
"""Update dialog showing release info and download link."""

import webbrowser

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.update_manager import CURRENT_VERSION, GITHUB_RELEASES_URL, pick_windows_asset


class UpdateDialog(QDialog):
    """Dialog to display available update information with download link."""

    def __init__(
        self,
        version: str,
        changelog: str,
        assets: list,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.version = version
        self.changelog = changelog
        self.assets = assets
        self._setup_ui()

    def _setup_ui(self):
        """Build the dialog UI."""
        self.setWindowTitle("Update Available")
        self.setMinimumSize(500, 420)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel(f"<h2>Update Available: v{self.version}</h2>")
        header.setStyleSheet("color: #EAEAF0;")
        layout.addWidget(header)

        # Current version info
        current = QLabel(f"Current version: <b>v{CURRENT_VERSION}</b>")
        current.setStyleSheet("color: #8B8BA0; font-size: 13px;")
        layout.addWidget(current)

        # Changelog section
        changelog_label = QLabel("Release Notes:")
        changelog_label.setStyleSheet("font-weight: bold; color: #EAEAF0;")
        layout.addWidget(changelog_label)

        # Scrollable changelog
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: 1px solid #3A3A50; border-radius: 8px; background-color: #1A1A24;")
        scroll.setMaximumHeight(200)

        changelog_widget = QTextEdit()
        changelog_widget.setPlainText(self.changelog)
        changelog_widget.setReadOnly(True)
        changelog_widget.setStyleSheet(
            """
            QTextEdit {
                background-color: #1A1A24;
                color: #EAEAF0;
                border: none;
                padding: 12px;
                font-size: 13px;
                line-height: 1.5;
            }
            """
        )
        scroll.setWidget(changelog_widget)
        layout.addWidget(scroll)

        # Check if Windows asset is available
        windows_asset = pick_windows_asset(self.assets)
        has_windows_asset = windows_asset is not None

        # Asset info and direct link
        if has_windows_asset:
            asset_info = QLabel(f"✓ Windows installer: <b>{windows_asset['name']}</b>")
            asset_info.setStyleSheet("color: #1D9E75; font-size: 12px;")
            layout.addWidget(asset_info)

            # Direct download link
            direct_link = QLabel(
                f'<a href="{windows_asset["browser_download_url"]}">Direct download link</a>'
            )
            direct_link.setStyleSheet("color: #6C6CFF; font-size: 12px;")
            direct_link.setOpenExternalLinks(True)
            layout.addWidget(direct_link)
        else:
            asset_info = QLabel("✗ No Windows installer found in this release")
            asset_info.setStyleSheet("color: #FF6B6B; font-size: 12px;")
            layout.addWidget(asset_info)

        # Instructions
        instructions = QLabel(
            "<b>How to update:</b><br>"
            "1. Click 'Open Download Page' below<br>"
            "2. Download the new .exe file<br>"
            "3. Close this app<br>"
            "4. Run the new .exe file (your data will be preserved)<br>"
            "5. Delete the old .exe file"
        )
        instructions.setStyleSheet("color: #8B8BA0; font-size: 12px; margin-top: 8px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.later_btn = QPushButton("Later")
        self.later_btn.setProperty("class", "secondary")
        self.later_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.later_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.later_btn)

        button_layout.addStretch()

        self.open_page_btn = QPushButton("Open Download Page")
        self.open_page_btn.setProperty("class", "task-action-btn")
        self.open_page_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_page_btn.clicked.connect(self._open_download_page)
        button_layout.addWidget(self.open_page_btn)

        layout.addLayout(button_layout)

    def _open_download_page(self):
        """Open the GitHub releases page in browser."""
        webbrowser.open(GITHUB_RELEASES_URL)
        self.accept()

    def accept(self):
        """Accept the dialog."""
        super().accept()

    def reject(self):
        """Reject the dialog to skip update."""
        super().reject()
