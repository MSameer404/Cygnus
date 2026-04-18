# src/app/ui/widgets/report_dialog.py
"""Dialog for submitting bug reports and feature requests via Discord webhook."""

import json
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QMessageBox,
    QProgressDialog,
)


DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1495085743859830894/hDZZWME0_10QJkP0elgIC5EM9gx-AINrGP0M0fTQ7pTYQ_FP_N4Uug8sUEwCQNZZ2v1o"

REPORT_TYPES = {
    "Problem": {"emoji": "🐛", "color": 0xFF6B6B},
    "Suggestion": {"emoji": "💡", "color": 0x00CEC9},
}


class WebhookWorker(QThread):
    """Background worker to send report to Discord webhook."""

    finished = pyqtSignal(bool, str)

    def __init__(self, report_type: str, title: str, description: str):
        super().__init__()
        self.report_type = report_type
        self.title = title
        self.description = description

    def run(self):
        try:
            report_config = REPORT_TYPES.get(self.report_type, REPORT_TYPES["Problem"])
            title_text = f" - {self.title}" if self.title else ""

            # Build the embed payload
            embed = {
                "title": f"{report_config['emoji']} New {self.report_type}{title_text}",
                "description": self.description,
                "color": report_config["color"],
                "fields": [
                    {
                        "name": "Type",
                        "value": self.report_type,
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Cygnus Study Tracker"
                },
                "timestamp": datetime.now().isoformat()
            }

            payload = {
                "username": "Cygnus Reporter",
                "avatar_url": "https://cdn.discordapp.com/embed/avatars/0.png",
                "embeds": [embed]
            }

            data = json.dumps(payload).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Cygnus-Report/1.0"
            }
            req = Request(DISCORD_WEBHOOK_URL, data=data, headers=headers, method="POST")

            with urlopen(req, timeout=60) as response:
                if response.status in (200, 204):
                    self.finished.emit(True, "Report sent successfully!")
                else:
                    self.finished.emit(False, f"Server returned status {response.status}")

        except URLError as e:
            self.finished.emit(False, f"Network error: {str(e)}")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")

class ReportDialog(QDialog):
    """Dialog for users to submit bug reports and suggestions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Send Feedback")
        self.setMinimumSize(550, 500)
        self.resize(550, 520)
        self.setObjectName("reportDialog")
        self._worker: WebhookWorker | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Title
        title = QLabel("� Send Feedback")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #EAEAF0;")
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Found a bug or have an idea? Let us know and we'll improve Cygnus in future updates.")
        subtitle.setStyleSheet("font-size: 13px; color: #8B8BA0;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # Type selection - Big styled buttons
        type_layout = QHBoxLayout()
        type_layout.setSpacing(12)

        self._problem_btn = QPushButton("🐛  Problem")
        self._problem_btn.setCheckable(True)
        self._problem_btn.setChecked(True)
        self._problem_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._problem_btn.setStyleSheet(self._type_button_style("#FF6B6B"))
        self._problem_btn.clicked.connect(lambda: self._select_type("Problem"))
        type_layout.addWidget(self._problem_btn)

        self._suggestion_btn = QPushButton("💡  Suggestion")
        self._suggestion_btn.setCheckable(True)
        self._suggestion_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._suggestion_btn.setStyleSheet(self._type_button_style("#00CEC9"))
        self._suggestion_btn.clicked.connect(lambda: self._select_type("Suggestion"))
        type_layout.addWidget(self._suggestion_btn)

        layout.addLayout(type_layout)
        self._current_type = "Problem"

        layout.addSpacing(8)

        # Title input
        title_label = QLabel("Title")
        title_label.setStyleSheet("font-size: 13px; color: #EAEAF0; font-weight: 500;")
        layout.addWidget(title_label)

        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("Brief summary of your feedback...")
        self._title_edit.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D3A;
                color: #EAEAF0;
                border: 1px solid #3D3D4A;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #6C5CE7;
            }
        """)
        layout.addWidget(self._title_edit)

        layout.addSpacing(4)

        # Description
        desc_label = QLabel("What's on your mind?")
        desc_label.setStyleSheet("font-size: 13px; color: #EAEAF0; font-weight: 500;")
        layout.addWidget(desc_label)

        self._desc_edit = QTextEdit()
        self._desc_edit.setPlaceholderText("Describe the problem or your suggestion in detail. The more information, the better we can help!\n\nFor problems:\n• What happened?\n• What did you expect?\n• Steps to reproduce\n\nFor suggestions:\n• What's your idea?\n• How would it help you?")
        self._desc_edit.setStyleSheet("""
            QTextEdit {
                background-color: #2D2D3A;
                color: #EAEAF0;
                border: 1px solid #3D3D4A;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border: 1px solid #6C5CE7;
            }
        """)
        self._desc_edit.setMinimumHeight(180)
        layout.addWidget(self._desc_edit)

        layout.addSpacing(8)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3D3D4A;
                color: #EAEAF0;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #4D4D5A;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        self._submit_btn = QPushButton("Send Feedback")
        self._submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._submit_btn.setMinimumWidth(120)
        self._submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C5CE7;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5B4BD4;
            }
            QPushButton:disabled {
                background-color: #3D3D4A;
                color: #8B8BA0;
            }
        """)
        self._submit_btn.clicked.connect(self._submit_report)
        button_layout.addWidget(self._submit_btn)

        layout.addLayout(button_layout)

    def _select_type(self, report_type: str):
        """Handle report type selection."""
        self._current_type = report_type
        if report_type == "Problem":
            self._problem_btn.setChecked(True)
            self._suggestion_btn.setChecked(False)
            self._problem_btn.setStyleSheet(self._type_button_style("#FF6B6B", active=True))
            self._suggestion_btn.setStyleSheet(self._type_button_style("#00CEC9", active=False))
        else:
            self._problem_btn.setChecked(False)
            self._suggestion_btn.setChecked(True)
            self._problem_btn.setStyleSheet(self._type_button_style("#FF6B6B", active=False))
            self._suggestion_btn.setStyleSheet(self._type_button_style("#00CEC9", active=True))

    def _type_button_style(self, color: str, active: bool = True) -> str:
        """Generate style for type selection button."""
        if active:
            return f"""
                QPushButton {{
                    background-color: {color};
                    color: #FFFFFF;
                    border: 2px solid {color};
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: bold;
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {color};
                    border: 2px solid {color};
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {color}20;
                }}
            """

    def _submit_report(self):
        """Submit the report to Discord webhook."""
        description = self._desc_edit.toPlainText().strip()
        if not description:
            QMessageBox.warning(self, "Missing Description", "Please enter a description of the issue.")
            return

        report_type = self._current_type

        # Disable UI during submission
        self._submit_btn.setEnabled(False)
        self._submit_btn.setText("Sending...")

        title = self._title_edit.text().strip()

        # Create and start worker thread
        self._worker = WebhookWorker(report_type, title, description)
        self._worker.finished.connect(self._on_report_sent)
        self._worker.start()

    def _on_report_sent(self, success: bool, message: str):
        """Handle report submission result."""
        self._submit_btn.setEnabled(True)
        self._submit_btn.setText("Send Feedback")

        if success:
            QMessageBox.information(self, "Success", "Report sent successfully!\n\nThank you for helping us improve Cygnus.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to send report:\n{message}")
