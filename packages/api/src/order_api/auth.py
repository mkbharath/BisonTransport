"""Local JWT authentication for the Order Intelligence Platform."""

import hashlib
import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import text

from order_shared.db.session import async_session_factory

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "local-dev-secret-change-in-production")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

ROLE_HIERARCHY: dict[str, int] = {
    "readonly": 0,
    "agent": 1,
    "supervisor": 2,
    "admin": 3,
}

security = HTTPBearer()


class TokenPayload(BaseModel):
    sub: str
    email: str
    role: str
    name: str
    exp: datetime


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class CurrentUser(BaseModel):
    id: str
    email: str
    role: str
    name: str


def create_access_token(data: dict[str, Any]) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its SHA-256 hash."""
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """Decode JWT and return the current user. Used as a FastAPI dependency."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": {"code": "UNAUTHORIZED", "message": "Invalid or expired token"}},
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        if payload.get("type") != "access":
            raise credentials_exception
        return CurrentUser(
            id=user_id,
            email=payload.get("email", ""),
            role=payload.get("role", "readonly"),
            name=payload.get("name", ""),
        )
    except JWTError:
        raise credentials_exception


def require_role(minimum_role: str):
    """Decorator/dependency factory that enforces minimum role level."""

    minimum_level = ROLE_HIERARCHY.get(minimum_role, 0)

    def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        user_level = ROLE_HIERARCHY.get(current_user.role, 0)
        if user_level < minimum_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": f"Requires at least '{minimum_role}' role",
                    }
                },
            )
        return current_user

    return role_checker


async def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    """Authenticate user by email/password. Returns user dict or None."""
    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT id, email, name, role, password_hash, active FROM users WHERE email = :email"),
            {"email": email},
        )
        user = result.mappings().first()
        if not user:
            return None
        if not user["active"]:
            return None
        if not user["password_hash"]:
            return None
        if not verify_password(password, user["password_hash"]):
            return None
        # Update last_login_at
        await session.execute(
            text("UPDATE users SET last_login_at = NOW() WHERE id = :id"),
            {"id": str(user["id"])},
        )
        await session.commit()
        return dict(user)
