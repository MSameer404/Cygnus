# src/app/ui/contact_dialog.py
"""Contact Us dialog for the application."""

import webbrowser

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

GITHUB_URL = "https://github.com/MohammadSameer-Dev/Cygnus"


class ContactDialog(QDialog):
    """Dialog showing developer contact information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Contact Us")
        self.setFixedSize(480, 420)
        self.setObjectName("contactDialog")
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # Title
        title = QLabel("Contact Us")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Segoe UI", 20)
        font.setBold(True)
        title.setFont(font)
        root.addWidget(title)

        separator = QLabel("============================")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        separator.setStyleSheet("color: #8B8BA0; font-family: monospace;")
        root.addWidget(separator)

        # Subtitle
        subtitle = QLabel("Made by Mohammad Sameer with Love")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont("Segoe UI", 12)
        subtitle_font.setItalic(True)
        subtitle.setFont(subtitle_font)
        root.addWidget(subtitle)

        # Description
        desc = QLabel(
            "Have a question, suggestion, or just want to say hello? "
            "Feel free to reach out through any of the channels below — "
            "we'd love to hear from you."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #C0C0D0; margin-bottom: 8px; margin-top: 8px;")
        root.addWidget(desc)

        # Details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(8)

        details = [
            ("Email", "mohammad.sameer@myyahoo.com"),
            ("Reddit", "u/UrbanSabhuOriginal"),
            ("Discord", "@iamsmr"),
        ]

        for label_text, value_text in details:
            text = f"<b>{label_text.ljust(8)} :</b> {value_text}"
            lbl = QLabel(text)
            lbl.setStyleSheet("font-family: Consolas, 'Courier New', monospace; font-size: 14px;")
            details_layout.addWidget(lbl)

        root.addLayout(details_layout)

        # Go to GitHub button
        github_btn = QPushButton("🐙 Go to GitHub")
        github_btn.setProperty("class", "task-action-btn")
        github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        github_btn.clicked.connect(self._open_github)
        github_btn.setStyleSheet("margin-top: 12px;")
        root.addWidget(github_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Footer
        footer = QLabel("Hope you like our app! ❤️")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("margin-top: 16px; font-weight: bold; font-size: 14px;")
        root.addWidget(footer)

        root.addStretch()

    def _open_github(self):
        """Open GitHub repository in browser."""
        webbrowser.open(GITHUB_URL)
