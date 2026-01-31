"""
NEURAXIS AI Service - Test Fixtures
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers():
    """Create mock authentication headers."""
    return {"Authorization": "Bearer mock-token"}
