"""Process / dashboard schemas (mirror openapi Dashboard, ModuleCard)."""

from __future__ import annotations

from app.models.enums import ModuleStatus
from app.schemas.common import CamelModel


class CreateProcessRequest(CamelModel):
    # Accepts camelCase (processDefKey/customerName/customerOrg) via CamelModel
    # alias generator; also accepts snake_case by field name.
    process_def_key: str
    customer_name: str
    customer_org: str | None = None


class ProcessSummary(CamelModel):
    id: str
    customer_name: str | None = None
    customer_org: str | None = None
    status: str


class ModuleCard(CamelModel):
    module_instance_id: str
    key: str
    name: str
    explainer: str | None = None
    status: ModuleStatus
    progress: int
    responsible_role: str | None = None
    estimated_effort: str | None = None
    locked: bool
    unlock_hint: str | None = None
    next_action: str | None = None


class Dashboard(CamelModel):
    process_instance_id: str
    customer_name: str | None = None
    overall_progress: int
    modules: list[ModuleCard]
