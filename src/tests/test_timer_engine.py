# src/tests/test_timer_engine.py
"""Tests for TimerEngine."""

import time

import pytest
from PyQt6.QtWidgets import QApplication

from app.core.timer_engine import TimerEngine, TimerState


@pytest.fixture(scope="module")
def qapp():
    """Create a QApplication for test lifetime."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def engine(qapp):
    return TimerEngine()


def test_initial_state(engine):
    assert engine.state == TimerState.IDLE
    assert engine.elapsed_seconds == 0
    assert engine.start_time is None


def test_start_changes_state(engine):
    engine.start()
    assert engine.state == TimerState.RUNNING
    assert engine.start_time is not None
    engine.reset()


def test_pause_changes_state(engine):
    engine.start()
    engine.pause()
    assert engine.state == TimerState.PAUSED
    engine.reset()


def test_stop_returns_to_idle(engine):
    engine.start()
    start, end, duration = engine.stop()
    assert engine.state == TimerState.IDLE
    assert start is not None
    assert end is not None


def test_reset_clears_everything(engine):
    engine.start()
    engine.reset()
    assert engine.state == TimerState.IDLE
    assert engine.elapsed_seconds == 0
    assert engine.start_time is None


def test_format_seconds():
    assert TimerEngine.format_seconds(0) == "00:00:00"
    assert TimerEngine.format_seconds(61) == "00:01:01"
    assert TimerEngine.format_seconds(3661) == "01:01:01"


def test_format_seconds_short():
    assert TimerEngine.format_seconds_short(0) == "0m"
    assert TimerEngine.format_seconds_short(3600) == "1h 0m"
    assert TimerEngine.format_seconds_short(5400) == "1h 30m"
