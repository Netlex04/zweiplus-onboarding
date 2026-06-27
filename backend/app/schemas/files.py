"""File upload schema."""

from __future__ import annotations

from app.schemas.common import CamelModel


class FileUploadOut(CamelModel):
    id: str
    original_name: str
    content_type: str | None = None
    size_bytes: int
    question_key: str | None = None
