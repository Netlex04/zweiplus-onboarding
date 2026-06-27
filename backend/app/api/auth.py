"""Auth router: POST /api/auth/login."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import create_access_token
from app.config import Settings, get_settings
from app.db.session import get_session
from app.models import User
from app.security import verify_password
from app.schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    user = session.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültige Anmeldedaten",
        )
    token = create_access_token(user, settings)
    return LoginResponse(token=token, role=user.role, name=user.name)
