"""Email+password authentication: argon2 hashing + PyJWT (HS256) bearer tokens.

Follows the FastAPI security tutorial: pwdlib[argon2] for hashing, PyJWT for the
signed token, OAuth2PasswordBearer to pull the token off the Authorization header.
JWT_SECRET MUST be set in prod (.env.local locally, Cloud Run secret in prod); the
dev fallback exists only so tests/local runs work without configuration.
"""
from __future__ import annotations

import datetime as dt
import os
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from .deps import get_store
from .store import Store

_pwd = PasswordHash.recommended()  # argon2

JWT_SECRET = os.getenv("JWT_SECRET", "dev-insecure-secret-change-me-in-production-32b+")
JWT_ALG = "HS256"
DEFAULT_TTL_MIN = int(os.getenv("JWT_TTL_MINUTES", str(7 * 24 * 60)))  # 7 days

# auto_error=False -> missing token returns None (we raise 401, not 403).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

_UNAUTH = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd.verify(password, password_hash)


def create_access_token(sub: str, ttl_minutes: Optional[int] = None) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    ttl = DEFAULT_TTL_MIN if ttl_minutes is None else ttl_minutes
    payload = {"sub": sub, "iat": now, "exp": now + dt.timedelta(minutes=ttl)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    store: Store = Depends(get_store),
) -> dict:
    if not token:
        raise _UNAUTH
    try:
        sub = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG]).get("sub")
    except jwt.PyJWTError:
        raise _UNAUTH from None
    if not sub:
        raise _UNAUTH
    user = store.get_user(sub)
    if user is None:
        raise _UNAUTH
    return user
