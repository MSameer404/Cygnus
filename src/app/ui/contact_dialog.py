# src/app/ui/contact_dialog.py
"""Contact Us dialog for the application."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
)


class ContactDialog(QDialog):
    """Dialog showing developer contact information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Contact Us")
        self.setFixedSize(480, 400)
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
            ("GitHub", "https://github.com/MohammadSameer-Dev/Cygnus/tree/master"),
        ]

        for label_text, value_text in details:
            if value_text.startswith("http"):
                text = f"<b>{label_text.ljust(8)} :</b> <a href='{value_text}' style='color: #4DA8DA; text-decoration: none;'>{value_text}</a>"
            else:
                text = f"<b>{label_text.ljust(8)} :</b> {value_text}"
            
            lbl = QLabel(text)
            lbl.setTextFormat(Qt.TextFormat.RichText)
            lbl.setOpenExternalLinks(True)
            lbl.setStyleSheet("font-family: Consolas, 'Courier New', monospace; font-size: 14px;")
            details_layout.addWidget(lbl)

        root.addLayout(details_layout)

        # Footer
        footer = QLabel("Hope you like our app! ❤️")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("margin-top: 16px; font-weight: bold; font-size: 14px;")
        root.addWidget(footer)
        
        root.addStretch()
