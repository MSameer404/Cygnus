# src/app/core/events.py
"""Global application events for cross-component communication."""

from PyQt6.QtCore import QObject, pyqtSignal


class AppEvents(QObject):
    """Central event bus for app-wide notifications."""

    # Emitted when all data is reset to default
    data_reset = pyqtSignal()


# Global singleton instance
app_events = AppEvents()
