"""Machine-to-machine authentication via a shared API key."""
import os

from fastapi import Header, HTTPException, status

from app.config import settings


async def require_simulator_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    """Allow access only if the X-API-Key header matches SIMULATOR_API_KEY.

    Returns 401 if the key is missing or does not match. If SIMULATOR_API_KEY
    is unset on the server, all requests are rejected (fail closed).
    """
    expected = settings.simulator_api_key
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Server has no simulator API key configured.",
        )
    if not x_api_key or x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header.",
        )