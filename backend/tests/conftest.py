import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
@pytest.fixture(scope="session")
def seeded_db() -> None:
    """Ensure seed data exists before Phase 2 integration tests run."""
    from sqlalchemy import select

    from app.database import SessionLocal
    from app.db.seed import seed
    from app.models.greenhouse import Greenhouse

    with SessionLocal() as db:
        if db.scalar(select(Greenhouse).limit(1)) is None:
            seed(db)