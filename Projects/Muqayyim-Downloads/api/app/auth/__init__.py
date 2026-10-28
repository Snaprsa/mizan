"""
Simple JWT auth for MVP. Structured for RBAC expansion later.
For dev: uses a default user if no auth header present.
"""

from datetime import datetime, timedelta

import uuid
from fastapi import HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.app.database import get_db
from api.app.models import User
from jose import JWTError, jwt

from api.app.config import get_settings

settings = get_settings()

# Default dev user (used when no auth header is present in dev mode)
DEV_USER = {
    "id": "00000000-0000-0000-0000-000000000001",
    "email": "dev@muqayyim.local",
    "name": "Dev User",
    "role": "admin",
}


def create_token(user_id: str, email: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiry_hours)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    """Persist local dev identity; signed tokens must refer to an active database user."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        if settings.env != "development":
            raise HTTPException(status_code=401, detail="Missing authentication")
        identity = uuid.UUID(DEV_USER["id"])
        row = await db.get(User, identity)
        if row is None:
            row = User(id=identity, email=DEV_USER["email"], name=DEV_USER["name"], role=DEV_USER["role"])
            db.add(row)
            await db.flush()
    else:
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        payload = decode_token(auth_header[7:])
        try:
            identity = uuid.UUID(payload["sub"])
        except (ValueError, KeyError, TypeError):
            raise HTTPException(status_code=401, detail="Invalid token subject")
        row = await db.get(User, identity)
    if row is None or not row.is_active:
        raise HTTPException(status_code=401, detail="Inactive or unknown user")
    return {"id": str(row.id), "email": row.email, "name": row.name, "role": row.role}
