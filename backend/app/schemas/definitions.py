"""Process/Module definition schemas."""

from __future__ import annotations

from app.schemas.common import CamelModel


class ModuleDefinitionSummary(CamelModel):
    key: str
    name: str
    short_description: str | None = None
    responsible_role: str | None = None
    estimated_effort: str | None = None


class ProcessDefinitionOut(CamelModel):
    key: str
    name: str
    description: str | None = None
    modules: list[ModuleDefinitionSummary] = []
