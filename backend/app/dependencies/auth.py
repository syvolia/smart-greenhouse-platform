"""FastAPI dependencies for authentication and role-based access control."""
from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.services.security import decode_access_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token"
        )
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
        )
    return user


def require_role(*allowed: UserRole) -> Callable[[User], User]:
    """Dependency factory: only the given roles may access the endpoint."""
    allowed_set = set(allowed)

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{user.role.value}' is not permitted to access this "
                    f"resource."
                ),
            )
        return user

    return dependency


# Convenience: any authenticated user
def any_user(user: User = Depends(get_current_user)) -> User:
    return user


# Convenience: admin or manager
require_manager = require_role(UserRole.ADMIN, UserRole.MANAGER)

# Admin or manager or agronomist (the "can act on alerts/recommendations" set)
require_agronomist = require_role(
    UserRole.ADMIN, UserRole.MANAGER, UserRole.AGRONOMIST
)

# Admin only
require_admin = require_role(UserRole.ADMIN)