
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add the app directory to Python's import path
APP_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIR))

from main import app
from utils.auth import get_current_user


@pytest.fixture
def client():
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides.clear()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)


@pytest.fixture
def authenticated_client():
    original_overrides = app.dependency_overrides.copy()

    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": 1,
        "email": "test@example.com"
    }

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)
