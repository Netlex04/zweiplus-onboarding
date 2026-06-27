"""Template schema (rendered email/text)."""

from __future__ import annotations

from app.schemas.common import CamelModel


class TemplateOut(CamelModel):
    key: str
    type: str
    title: str
    subject: str | None = None
    body: str | None = None
    file_name: str | None = None
    file_type: str | None = None
