# src/app/ui/widgets/sidebar.py
"""Vertical icon sidebar for page navigation."""

from pathlib import Path
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QWidget, QSpacerItem, QSizePolicy, QLabel, QHBoxLayout

from app.core.update_manager import CURRENT_VERSION


class Sidebar(QWidget):
    """Vertical navigation sidebar with icon buttons."""

    page_changed = pyqtSignal(int)
    profile_clicked = pyqtSignal()

    # Icon files for each page (stored in assets/icons/)
    PAGES = [
        ("home.ico", "Dashboard"),
        ("time.ico", "Time Tracker"),
        ("task.ico", "Task Tracker"),
        ("syllabus.ico", "Syllabus"),
        ("test.ico", "Test Tracker"),
        ("setting.ico", "Settings"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(64)
        self._buttons: list[QPushButton] = []
        self._active_index = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---------- Header Section (60px) ----------
        header = QWidget()
        header.setFixedHeight(60)
        header.setObjectName("sidebarHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        # App logo / brand — clickable, opens profile
        brand = QPushButton()
        brand.setProperty("class", "sidebar-btn")
        brand.setToolTip("View Profile")
        brand.setCursor(Qt.CursorShape.PointingHandCursor)
        brand.clicked.connect(self.profile_clicked.emit)
        brand.setFixedSize(64, 60)
        
        assets_dir = Path(__file__).parent.parent.parent / "assets"
        icon_ico = assets_dir / "logo.ico"
        icon_png = assets_dir / "logo.png"

        if icon_ico.exists():
            brand.setIcon(QIcon(str(icon_ico)))
            brand.setIconSize(QSize(32, 32))
            brand.setStyleSheet("border: none; background: transparent;")
        elif icon_png.exists():
            brand.setIcon(QIcon(str(icon_png)))
            brand.setIconSize(QSize(32, 32))
            brand.setStyleSheet("border: none; background: transparent;")
        else:
            brand.setText("📖")
            brand.setStyleSheet("font-size: 24px; border: none; background: transparent;")
        header_layout.addWidget(brand, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Horizontal separator line below header
        horizontal_line = QFrame()
        horizontal_line.setObjectName("headerSeparator")
        horizontal_line.setFrameShape(QFrame.Shape.HLine)
        horizontal_line.setFixedHeight(1)
        layout.addWidget(horizontal_line)

        # ---------- Navigation Section ----------
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(8, 12, 8, 16)
        nav_layout.setSpacing(12)

        # Navigation buttons
        icons_dir = assets_dir / "icons"
        for i, (icon_file, tooltip) in enumerate(self.PAGES):
            btn = QPushButton()
            btn.setProperty("class", "sidebar-btn")
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedSize(48, 48)

            icon_path = icons_dir / icon_file
            if icon_path.exists():
                btn.setIcon(QIcon(str(icon_path)))
                btn.setIconSize(QSize(32, 32))
                btn.setStyleSheet("QPushButton { border: none; background: transparent; text-align: center; padding: 0px; }")
            else:
                # Fallback to emoji if icon file missing
                emoji_fallback = ["🏠", "⏱️", "✅", "📖", "⚙️"][i]
                btn.setText(emoji_fallback)
                btn.setStyleSheet("QPushButton { font-size: 24px; border: none; background: transparent; text-align: center; padding: 0px; }")

            btn.clicked.connect(lambda checked, idx=i: self._on_click(idx))
            nav_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            self._buttons.append(btn)

        # Push remaining space to bottom
        nav_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Version label
        version_label = QLabel(f"v{CURRENT_VERSION}")
        version_label.setStyleSheet("color: #FF6B6B; font-size: 11px; margin-top: 6px;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(version_label, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(nav_container, stretch=1)
        self._update_active()

    def _on_click(self, index: int):
        self._active_index = index
        self._update_active()
        self.page_changed.emit(index)

    def _update_active(self):
        for i, btn in enumerate(self._buttons):
            btn.setProperty("active", "true" if i == self._active_index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def set_active(self, index: int):
        """Programmatically set the active page."""
        self._active_index = index
        self._update_active()
