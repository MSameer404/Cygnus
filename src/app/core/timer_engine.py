# src/app/core/timer_engine.py
"""QTimer-based stopwatch engine for study sessions."""

from enum import Enum, auto
from datetime import datetime

from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class TimerState(Enum):
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()


class TimerEngine(QObject):
    """Stopwatch engine that ticks every 100ms and emits elapsed seconds."""

    # Signals
    tick = pyqtSignal(int)           # elapsed_seconds
    state_changed = pyqtSignal(str)  # "idle" | "running" | "paused"
    session_finished = pyqtSignal(datetime, datetime, int)  # start, end, duration_s

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = TimerState.IDLE
        self._elapsed_ms = 0
        self._start_time: datetime | None = None
        self._last_tick_time: float | None = None

        self._timer = QTimer(self)
        self._timer.setInterval(100)  # 100ms ticks for smooth display
        self._timer.timeout.connect(self._on_tick)

    # ---------- Properties ----------

    @property
    def state(self) -> TimerState:
        return self._state

    @property
    def elapsed_seconds(self) -> int:
        return self._elapsed_ms // 1000

    @property
    def start_time(self) -> datetime | None:
        return self._start_time

    @property
    def is_running(self) -> bool:
        return self._state == TimerState.RUNNING

    # ---------- Controls ----------

    def start(self):
        """Start or resume the timer."""
        if self._state == TimerState.IDLE:
            self._elapsed_ms = 0
            self._start_time = datetime.now()

        if self._state in (TimerState.IDLE, TimerState.PAUSED):
            self._state = TimerState.RUNNING
            self._last_tick_time = self._now_ms()
            self._timer.start()
            self.state_changed.emit("running")

    def pause(self):
        """Pause the timer."""
        if self._state == TimerState.RUNNING:
            self._timer.stop()
            # Account for remaining time
            now = self._now_ms()
            self._elapsed_ms += int(now - self._last_tick_time)
            self._state = TimerState.PAUSED
            self.state_changed.emit("paused")

    def stop(self) -> tuple[datetime | None, datetime, int]:
        """Stop the timer and return (start_time, end_time, duration_seconds)."""
        self._timer.stop()
        end_time = datetime.now()

        if self._state == TimerState.RUNNING:
            now = self._now_ms()
            self._elapsed_ms += int(now - self._last_tick_time)

        duration = self._elapsed_ms // 1000
        start = self._start_time

        self._state = TimerState.IDLE
        self._last_tick_time = None

        self.state_changed.emit("idle")

        if start and duration > 0:
            self.session_finished.emit(start, end_time, duration)

        return start, end_time, duration

    def reset(self):
        """Reset without saving."""
        self._timer.stop()
        self._elapsed_ms = 0
        self._start_time = None
        self._last_tick_time = None
        self._state = TimerState.IDLE
        self.state_changed.emit("idle")
        self.tick.emit(0)

    # ---------- Internal ----------

    def _on_tick(self):
        now = self._now_ms()
        self._elapsed_ms += int(now - self._last_tick_time)
        self._last_tick_time = now
        self.tick.emit(self._elapsed_ms // 1000)

    @staticmethod
    def _now_ms() -> float:
        """Current time in milliseconds (monotonic-ish via datetime)."""
        import time
        return time.monotonic() * 1000

    # ---------- Formatting ----------

    @staticmethod
    def format_seconds(total_seconds: int) -> str:
        """Format seconds as HH:MM:SS."""
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    @staticmethod
    def format_seconds_short(total_seconds: int) -> str:
        """Format as Xh Ym or Xm Ys."""
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        if h > 0:
            return f"{h}h {m}m"
        return f"{m}m"
