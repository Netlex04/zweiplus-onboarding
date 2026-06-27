"""Authentication: JWT issuance + FastAPI dependencies (Architektur §11).

- ``create_access_token`` / ``decode_token`` — HS256 JWT signed with
  ``Settings.jwt_secret`` (python-jose).
- ``current_user`` — resolves the Bearer token to a ``User`` row.
- ``require_role(*roles)`` — dependency factory enforcing role-based access.

Customer-scoping (a customer may only see their own process) is enforced in the
process/module/step routers using ``current_user`` + ownership checks.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.session import get_session
from app.models import User
from app.models.enums import Role

ALGORITHM = "HS256"
TOKEN_TTL_HOURS = 12

_bearer = HTTPBearer(auto_error=False)


def create_access_token(
    user: User, settings: Settings | None = None, ttl_hours: int = TOKEN_TTL_HOURS
) -> str:
    settings = settings or get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "name": user.name,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=ttl_hours)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str, settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])


def _unauthorized(detail: str = "Nicht authentifiziert") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> User:
    if credentials is None or not credentials.credentials:
        raise _unauthorized()
    try:
        payload = decode_token(credentials.credentials, settings)
    except JWTError as exc:
        raise _unauthorized("Ungültiges oder abgelaufenes Token") from exc

    user_id = payload.get("sub")
    user = session.get(User, user_id) if user_id else None
    if user is None:
        raise _unauthorized("Benutzer nicht gefunden")
    return user


def require_role(*roles: Role):
    """Dependency factory: allow only the given roles."""
    allowed = {r.value if isinstance(r, Role) else r for r in roles}

    def _dependency(user: User = Depends(current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Keine Berechtigung für diese Aktion",
            )
        return user

    return _dependency
