"""User CRUD, login, and refresh-token rotation.

Refresh token strategy:
  - On login, we issue an access token (short-lived) and a refresh token
    (long-lived) whose SHA-256 hash is stored in the DB.
  - On refresh, the old token is marked revoked and a new one issued
    (rotation). Replay of a revoked token is rejected.
  - Logout revokes the presented refresh token.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.enums import UserRole
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.scalar(select(User).where(User.email == email.lower().strip()))


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.get(User, user_id)


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)).all())


def create_user(
    db: Session,
    *,
    email: str,
    password: str,
    full_name: str,
    role: UserRole = UserRole.VIEWER,
    is_active: bool = True,
) -> User:
    user = User(
        email=email.lower().strip(),
        full_name=full_name,
        hashed_password=hash_password(password),
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ---------------------------------------------------------------------------
# Token issuance
# ---------------------------------------------------------------------------


def _issue_refresh_token(db: Session, user: User) -> str:
    raw = generate_refresh_token()
    record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(record)
    db.commit()
    return raw


def issue_token_pair(db: Session, user: User) -> dict:
    access, expires_in = create_access_token(user.id, user.role.value)
    refresh = _issue_refresh_token(db, user)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


def rotate_refresh_token(db: Session, raw_refresh: str) -> Optional[dict]:
    """Validate a refresh token, revoke it, and issue a new pair.

    Returns None if the token is invalid, expired, or already revoked.
    """
    token_hash = hash_refresh_token(raw_refresh)
    record = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    if record is None or record.revoked:
        return None
    if record.expires_at < datetime.now(timezone.utc):
        record.revoked = True
        db.commit()
        return None

    user = db.get(User, record.user_id)
    if user is None or not user.is_active:
        record.revoked = True
        db.commit()
        return None

    # Revoke old, issue new
    record.revoked = True
    db.commit()

    return issue_token_pair(db, user)


def revoke_refresh_token(db: Session, raw_refresh: str) -> bool:
    token_hash = hash_refresh_token(raw_refresh)
    record = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    if record is None or record.revoked:
        return False
    record.revoked = True
    db.commit()
    return True


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------


def bootstrap_admin_if_needed(db: Session) -> None:
    """Create a bootstrap admin on first startup, if none exists.

    Reads BOOTSTRAP_ADMIN_EMAIL / BOOTSTRAP_ADMIN_PASSWORD from settings.
    Silent if either is missing or if any user already exists.
    """
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        return
    existing = db.scalar(select(User.id).limit(1))
    if existing is not None:
        return
    logger.warning(
        "Creating bootstrap admin '%s' — change the password immediately.",
        settings.bootstrap_admin_email,
    )
    create_user(
        db,
        email=settings.bootstrap_admin_email,
        password=settings.bootstrap_admin_password,
        full_name=settings.bootstrap_admin_full_name,
        role=UserRole.ADMIN,
        is_active=True,
    )