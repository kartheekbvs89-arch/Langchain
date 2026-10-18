"""Pytest configuration — ensure backend is on sys.path and seed DB once."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make app/ importable when running from tests/
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(scope="session", autouse=True)
def seed_db_once():
    """Seed the vector DB once before any test runs."""
    from app.ingestion.ingest import seed_sample_docs
    seed_sample_docs(force=True)
    yield
