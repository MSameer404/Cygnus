# src/tests/conftest.py
"""Shared test fixtures for Cygnus tests."""

import os
import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def test_db(tmp_path):
    """Create a fresh test database for each test."""
    import app.data.database as db_module

    # Override database path
    test_db_path = tmp_path / "test.db"
    db_module.DB_PATH = test_db_path

    from sqlmodel import create_engine, SQLModel
    engine = create_engine(f"sqlite:///{test_db_path}", echo=False)
    db_module._engine = engine

    # Re-initialize tables
    SQLModel.metadata.create_all(engine)

    yield

    # Dispose engine to release file locks (required on Windows)
    engine.dispose()
