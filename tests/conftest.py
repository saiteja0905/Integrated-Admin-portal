"""Test fixtures: run the FastAPI app against an in-memory MongoDB.

Install:  pip install -r backend/requirements-dev.txt
Run:      pytest tests      (from the repository root)
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "sanyuth_test")
os.environ.setdefault("JWT_SECRET", "test-secret-" + "x" * 40)
os.environ.setdefault("UPLOAD_DIR", tempfile.mkdtemp(prefix="sanyuth-uploads-"))

from fastapi.testclient import TestClient  # noqa: E402
from mongomock_motor import AsyncMongoMockClient  # noqa: E402

import server  # noqa: E402  (must be imported before admin_routes)
import admin_routes  # noqa: E402


@pytest.fixture()
def client():
    """A test client with a fresh in-memory database, seeded with the demo data."""
    mock_db = AsyncMongoMockClient()["sanyuth_test"]
    server.db = mock_db
    admin_routes.db = mock_db
    with TestClient(server.app) as test_client:
        yield test_client
