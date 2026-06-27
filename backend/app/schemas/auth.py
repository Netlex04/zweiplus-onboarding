"""Auth schemas."""

from __future__ import annotations

from pydantic import BaseModel

from app.models.enums import Role


class LoginRequest(BaseModel):
    # Plain str (email-validator not a dependency); format is documented in OpenAPI.
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: Role
    name: str | None = None
