from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test.db"
    from app.database import init_engine

    init_engine(f"sqlite:///{db_path.as_posix()}")
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        response = test_client.post(
            "/api/auth/signup",
            json={"email": "student@example.com", "password": "correct-horse", "display_name": "Student"},
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        test_client.headers.update({"Authorization": f"Bearer {token}"})
        yield test_client
