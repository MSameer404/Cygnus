# src/app/ui/widgets/sidebar.py
"""Vertical icon sidebar for page navigation."""

from pathlib import Path
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QWidget, QSpacerItem, QSizePolicy, QLabel, QHBoxLayout

from app.core.utils import CURRENT_VERSION
from app.data.settings_store import load_setting


class Sidebar(QWidget):
    """Vertical navigation sidebar with icon buttons."""

    page_changed = Signal(int)
    profile_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(64)
        self._buttons: list[QPushButton] = []
        self._page_indices: list[int] = []
        self._active_index = 0
        
        # Read trackers visibility
        self.show_trackers = load_setting("show_optional_trackers", False)
        
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
        
        from app.core.utils import get_assets_dir, get_icon_path
        assets_dir = get_assets_dir()
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

        # Navigation buttons mapping (icon_file, tooltip, page_idx, emoji_fallback)
        top_pages = [
            ("home.ico", "Dashboard", 0, "🏠"),
            ("time.ico", "Time Tracker", 1, "⏱️"),
            ("task.ico", "Task Tracker", 2, "✅"),
        ]
        
        if self.show_trackers:
            top_pages.append(("syllabus.ico", "Syllabus", 3, "📚"))
            top_pages.append(("test.ico", "Test Tracker", 4, "📝"))

        # Create Top Navigation buttons
        for icon_file, tooltip, page_idx, emoji in top_pages:
            btn = QPushButton()
            btn.setProperty("class", "sidebar-btn")
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedSize(48, 48)

            icon_path = get_icon_path(icon_file)
            if icon_path.exists():
                btn.setIcon(QIcon(str(icon_path)))
                btn.setIconSize(QSize(32, 32))
                btn.setStyleSheet("QPushButton { border: none; background: transparent; text-align: center; padding: 0px; }")
            else:
                btn.setText(emoji)
                btn.setStyleSheet("QPushButton { font-size: 24px; border: none; background: transparent; text-align: center; padding: 0px; }")

            btn.clicked.connect(lambda checked, idx=page_idx: self._on_click(idx))
            nav_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            self._buttons.append(btn)
            self._page_indices.append(page_idx)

        # Push remaining space to bottom (retains settings at the absolute bottom!)
        nav_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Create Bottom Navigation button (Settings)
        settings_btn = QPushButton()
        settings_btn.setProperty("class", "sidebar-btn")
        settings_btn.setToolTip("Settings")
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setFixedSize(48, 48)

        icon_path = get_icon_path("setting.ico")
        if icon_path.exists():
            settings_btn.setIcon(QIcon(str(icon_path)))
            settings_btn.setIconSize(QSize(32, 32))
            settings_btn.setStyleSheet("QPushButton { border: none; background: transparent; text-align: center; padding: 0px; }")
        else:
            settings_btn.setText("⚙️")
            settings_btn.setStyleSheet("QPushButton { font-size: 24px; border: none; background: transparent; text-align: center; padding: 0px; }")

        settings_btn.clicked.connect(lambda checked, idx=5: self._on_click(idx))
        nav_layout.addWidget(settings_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self._buttons.append(settings_btn)
        self._page_indices.append(5)

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
        for btn, page_idx in zip(self._buttons, self._page_indices):
            is_active = (page_idx == self._active_index)
            btn.setProperty("active", "true" if is_active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def set_active(self, index: int):
        """Programmatically set the active page."""
        self._active_index = index
        self._update_active()

    def reload_sidebar(self):
        """Clear layout and rebuild to dynamically toggle trackers."""
        self.show_trackers = load_setting("show_optional_trackers", False)
        
        # Clear buttons tracking list
        self._buttons.clear()
        self._page_indices.clear()

        # Safely reparent old layout to a temporary widget to completely wipe the layout and widgets
        if self.layout() is not None:
            QWidget().setLayout(self.layout())

        # Re-build layout structure
        self._setup_ui()
