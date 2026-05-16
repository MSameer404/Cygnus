# src/app/core/events.py
"""Global application events for cross-component communication."""

from PySide6.QtCore import QObject, Signal


class AppEvents(QObject):
    """Central event bus for app-wide notifications."""

    # Emitted when all data is reset to default
    data_reset = Signal()


# Global singleton instance
app_events = AppEvents()
