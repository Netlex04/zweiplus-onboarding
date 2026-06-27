"""Module detail schema."""

from __future__ import annotations

from app.models.enums import ModuleStatus, StepStatus
from app.schemas.common import CamelModel
from app.schemas.template import TemplateOut


class ModuleIntro(CamelModel):
    goal: str | None = None
    why: str | None = None
    who: str | None = None
    effort: str | None = None
    explainer: str | None = None


class ModuleStepSummary(CamelModel):
    step_instance_id: str
    key: str
    title: str
    status: StepStatus


class ModuleDetail(CamelModel):
    module_instance_id: str
    key: str
    name: str
    intro: ModuleIntro | None = None
    status: ModuleStatus
    progress: int
    steps: list[ModuleStepSummary]
    templates: list[TemplateOut] = []
