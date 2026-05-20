# src/app/core/background_manager.py
"""Background image manager with blur and opacity support."""

import shutil
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor
from PySide6.QtWidgets import QApplication

from app.data.settings_store import load_setting, save_setting
from app.core.utils import get_assets_dir

_BG_STORE = Path(__file__).parent.parent / "data" / "bg_image.dat"
_SETTINGS_KEY_ENABLED = "bg_image_enabled"
_SETTINGS_KEY_BLUR = "bg_image_blur"
_SETTINGS_KEY_OPACITY = "bg_image_opacity"


def get_bg_image_path() -> Path:
    """Return the stored background image path."""
    return _BG_STORE


def save_bg_image(source_path: str) -> bool:
    """Copy an image file into the app's data directory."""
    src = Path(source_path)
    if not src.exists():
        return False
    _BG_STORE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, _BG_STORE)
    save_setting(_SETTINGS_KEY_ENABLED, True)
    return True


def remove_bg_image():
    """Remove the background image and disable the feature."""
    if _BG_STORE.exists():
        _BG_STORE.unlink()
    save_setting(_SETTINGS_KEY_ENABLED, False)


def is_bg_enabled() -> bool:
    return load_setting(_SETTINGS_KEY_ENABLED, False) and _BG_STORE.exists()


def get_blur_radius() -> int:
    return int(load_setting(_SETTINGS_KEY_BLUR, 20))


def get_opacity() -> float:
    return float(load_setting(_SETTINGS_KEY_OPACITY, 0.3))


def save_blur(radius: int):
    save_setting(_SETTINGS_KEY_BLUR, radius)


def save_opacity(opacity: float):
    save_setting(_SETTINGS_KEY_OPACITY, opacity)


def _stack_blur(image: QImage, radius: int) -> QImage:
    """Apply a mathematically perfect Pillow-based Gaussian Blur. Radius 0 = no blur."""
    if radius <= 0:
        return image

    try:
        from PIL import Image as PILImage, ImageFilter
        
        # Ensure format is ARGB32 for consistent byte layout
        img = image.convertToFormat(QImage.Format.Format_ARGB32)
        width, height = img.width(), img.height()
        
        # Retrieve direct memory bytes from the QImage
        ptr = img.bits()
        bytes_data = bytes(ptr)
        
        # Load into PIL (BGRA format raw pixel stream)
        pil_img = PILImage.frombytes("RGBA", (width, height), bytes_data, "raw", "BGRA")
        
        # Apply true distortion-free Gaussian Blur
        blurred_pil = pil_img.filter(ImageFilter.GaussianBlur(radius))
        
        # Convert back to raw bytes
        blurred_bytes = blurred_pil.tobytes("raw", "BGRA")
        
        # Wrap into QImage and perform a deep copy to ensure memory safety
        return QImage(blurred_bytes, width, height, QImage.Format.Format_ARGB32).copy()
    except Exception as e:
        # Graceful fallback: downscale/upscale box approximation if PIL is unavailable
        img = image.convertToFormat(QImage.Format.Format_ARGB32)
        w, h = img.width(), img.height()
        scale = max(1, min(radius, 40))
        small_w = max(1, w // (scale + 1))
        small_h = max(1, h // (scale + 1))
        
        small = img.scaled(
            small_w, small_h,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        return small.scaled(
            w, h,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )


def build_background_pixmap(width: int, height: int) -> QPixmap | None:
    """
    Build a composited background pixmap:
    - Scaled & cropped to fill (width x height)
    - Blurred by the configured radius
    - Dimmed by overlay opacity
    """
    if not is_bg_enabled():
        return None

    raw = QImage(str(_BG_STORE))
    if raw.isNull():
        return None

    # Scale to cover the full window
    scaled = raw.scaled(
        width, height,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation
    )

    # Center-crop
    x_off = (scaled.width() - width) // 2
    y_off = (scaled.height() - height) // 2
    cropped = scaled.copy(x_off, y_off, width, height)

    # Apply blur
    blurred = _stack_blur(cropped, get_blur_radius())

    # Composite: draw dark overlay on top to darken
    result = QPixmap(width, height)
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.drawImage(0, 0, blurred)
    opacity = 1.0 - get_opacity()   # opacity=0.3 → overlay 70% dim
    painter.fillRect(0, 0, width, height, QColor(0, 0, 0, int(opacity * 255)))
    painter.end()

    return result


def apply_to_window(window):
    """Paint the background image into the main window's palette."""
    from PySide6.QtGui import QPalette, QBrush
    if not is_bg_enabled():
        window.setAutoFillBackground(False)
        window.centralWidget().setAutoFillBackground(False)
        return

    px = build_background_pixmap(window.width(), window.height())
    if not px:
        return

    palette = window.palette()
    palette.setBrush(QPalette.ColorRole.Window, QBrush(px))
    window.setPalette(palette)
    window.setAutoFillBackground(True)
