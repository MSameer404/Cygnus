# src/app/ui/widgets/sidebar.py
"""Vertical icon sidebar for page navigation."""

from pathlib import Path
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QWidget, QSpacerItem, QSizePolicy


class Sidebar(QWidget):
    """Vertical navigation sidebar with icon buttons."""

    page_changed = pyqtSignal(int)

    # Unicode icons for each page
    PAGES = [
        ("🏠", "Dashboard"),
        ("⏱️", "Timer"),
        ("📊", "Statistics"),
        ("✅", "Todos"),
        ("⚙️", "Settings"),
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
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(4)

        # App logo / brand
        brand = QPushButton()
        brand.setProperty("class", "sidebar-btn")
        brand.setToolTip("Cygnus Study")
        brand.setEnabled(False)
        
        assets_dir = Path(__file__).parent.parent.parent / "assets"
        icon_ico = assets_dir / "logo.ico"
        icon_png = assets_dir / "logo.png"

        if icon_ico.exists():
            brand.setIcon(QIcon(str(icon_ico)))
            brand.setIconSize(QSize(28, 28))
            brand.setStyleSheet("opacity: 0.5; border: none; background: transparent;")
        elif icon_png.exists():
            brand.setIcon(QIcon(str(icon_png)))
            brand.setIconSize(QSize(28, 28))
            brand.setStyleSheet("opacity: 0.5; border: none; background: transparent;")
        else:
            brand.setText("📖")
            brand.setStyleSheet("font-size: 22px; opacity: 0.5; border: none; background: transparent;")
        layout.addWidget(brand, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(16)

        # Navigation buttons
        for i, (icon, tooltip) in enumerate(self.PAGES):
            btn = QPushButton(icon)
            btn.setProperty("class", "sidebar-btn")
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=i: self._on_click(idx))
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            self._buttons.append(btn)

        # Push remaining space to bottom
        layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

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
