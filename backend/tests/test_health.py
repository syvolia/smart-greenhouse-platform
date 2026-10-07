from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.database import get_db
from app.main import app


def test_liveness(client: TestClient) -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_readiness_connected(client: TestClient) -> None:
    class FakeSession:
        def execute(self, *_args, **_kwargs):
            return None

    app.dependency_overrides[get_db] = lambda: FakeSession()
    try:
        response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "connected"}


def test_readiness_disconnected(client: TestClient) -> None:
    class FailingSession:
        def execute(self, *_args, **_kwargs):
            raise OperationalError("boom", {}, Exception("boom"))

    app.dependency_overrides[get_db] = lambda: FailingSession()
    try:
        response = client.get("/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "unready", "database": "disconnected"}
