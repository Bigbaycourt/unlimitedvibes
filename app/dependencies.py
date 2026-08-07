"""
Shared dependencies for FastAPI routes.
"""

from fastapi import Depends, Header, HTTPException, status
from typing import Optional


# Valid tokens for development/testing
VALID_TOKENS = {"test-token", "admin-token"}
ADMIN_TOKENS = {"admin-token"}


async def require_auth(
    authorization: Optional[str] = Header(None),
) -> str:
    """
    Validate Bearer token from Authorization header.

    Returns the token string if valid.
    Raises 401 if missing or invalid.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization format. Use: Bearer <token>",
        )

    token = authorization.removeprefix("Bearer ").strip()

    if token not in VALID_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return token


async def require_admin(
    authorization: Optional[str] = Header(None),
) -> str:
    """
    Validate that the token has admin-level access.

    Raises 401 if missing/invalid, 403 if not admin.
    """
    token = await require_auth(authorization)

    if token not in ADMIN_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return token
