"""Shared schema base + error response."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base model: camelCase JSON aliases, populated by field name internally."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
