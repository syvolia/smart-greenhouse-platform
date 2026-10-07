import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database import SessionLocal
from app.models.enums import UserRole
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.security import hash_password


@pytest.fixture
def clean_users(seeded_db: None):
    with SessionLocal() as db:
        db.execute(delete(RefreshToken))
        db.execute(delete(User))
        db.commit()
        # Create one user per role for tests
        for role in UserRole:
            db.add(User(
                email=f"{role.value}@test.local",
                full_name=f"{role.value.title()} User",
                hashed_password=hash_password("password123"),
                role=role,
                is_active=True,
            ))
        db.commit()
    yield
    with SessionLocal() as db:
        db.execute(delete(RefreshToken))
        db.execute(delete(User))
        db.commit()


def _login(client: TestClient, email: str, password: str = "password123"):
    return client.post("/auth/login", json={"email": email, "password": password})


def test_login_success(client, clean_users):
    r = _login(client, "admin@test.local")
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0


def test_login_wrong_password(client, clean_users):
    r = _login(client, "admin@test.local", "wrong")
    assert r.status_code == 401


def test_login_unknown_email(client, clean_users):
    r = _login(client, "nobody@test.local")
    assert r.status_code == 401


def test_me_returns_current_user(client, clean_users):
    token = _login(client, "manager@test.local").json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "manager@test.local"
    assert r.json()["role"] == "manager"


def test_me_without_token_is_401(client, clean_users):
    assert client.get("/auth/me").status_code == 401


def test_me_with_bad_token_is_401(client, clean_users):
    r = client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401


def test_refresh_rotates_tokens(client, clean_users):
    pair = _login(client, "viewer@test.local").json()
    r = client.post("/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    assert r.status_code == 200
    new_pair = r.json()
    assert new_pair["refresh_token"] != pair["refresh_token"]

    # Old refresh token must be rejected now
    replay = client.post("/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    assert replay.status_code == 401


def test_logout_revokes_refresh(client, clean_users):
    pair = _login(client, "viewer@test.local").json()
    r = client.post("/auth/logout", json={"refresh_token": pair["refresh_token"]})
    assert r.status_code == 204
    # After logout, refresh must fail
    r = client.post("/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    assert r.status_code == 401


def test_admin_can_create_users(client, clean_users):
    token = _login(client, "admin@test.local").json()["access_token"]
    r = client.post(
        "/auth/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "new@test.local",
            "full_name": "New User",
            "password": "another-password",
            "role": "viewer",
        },
    )
    assert r.status_code == 201
    assert r.json()["email"] == "new@test.local"


def test_non_admin_cannot_create_users(client, clean_users):
    token = _login(client, "manager@test.local").json()["access_token"]
    r = client.post(
        "/auth/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "x@test.local",
            "full_name": "X",
            "password": "password123",
            "role": "viewer",
        },
    )
    assert r.status_code == 403