"""
src/security.py
---------------
JWT validation for FastAPI.

FastAPI and Spring Boot share the same JWT_SECRET (set in .env).
Spring Boot mints the token on login; FastAPI validates it on every
protected request. No round-trip between services needed — the shared
secret is sufficient for stateless validation.

Usage in routes:
    from src.security import get_current_user

    @router.post("/qa")
    async def qa(body: QARequest, user=Depends(get_current_user)):
        ...  # user is the decoded JWT payload dict
"""

import os
from typing import Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

ALGORITHM = "HS256"
_bearer = HTTPBearer()


def _get_secret() -> str:
    secret = os.getenv("JWT_SECRET", "finsight-super-secret-key-change-in-production-minimum-32-chars")
    return secret


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> Dict[str, Any]:
    """
    FastAPI dependency — validates the Bearer JWT and returns the payload.

    Raises 401 if the token is missing, expired, or signed with a wrong secret.
    Inject this into any route that should require auth:

        @router.post("/upload")
        async def upload(..., user=Depends(get_current_user)):
            user_id = user["userId"]
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, _get_secret(), algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )