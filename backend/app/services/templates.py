"""Template resolution + placeholder rendering (FR-TPL-002).

Templates are linked to modules/steps by ``(scope, owner_key)`` (no FK).
Placeholders use ``{{Name}}`` syntax. The render context is derived from the
optional ``moduleInstanceId`` (customer name, module name, …).
"""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    ModuleDefinition,
    ModuleInstance,
    ProcessInstance,
    StepDefinition,
    TemplateDefinition,
)

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")


def templates_for_owner(
    session: Session, scope: str, owner_key: str
) -> list[TemplateDefinition]:
    return list(
        session.scalars(
            select(TemplateDefinition).where(
                TemplateDefinition.scope == scope,
                TemplateDefinition.owner_key == owner_key,
            )
        )
    )


def templates_for_module(
    session: Session, module_def: ModuleDefinition
) -> list[TemplateDefinition]:
    """All templates for a module: module-scoped + every step-scoped one."""
    result = templates_for_owner(session, "module", module_def.key)
    step_keys = [s.key for s in module_def.steps]
    for key in step_keys:
        result.extend(templates_for_owner(session, "step", key))
    return result


def build_context(session: Session, module_instance_id: str | None) -> dict[str, str]:
    """Render context for placeholders. Empty if no module instance given."""
    if not module_instance_id:
        return {}
    module = session.get(ModuleInstance, module_instance_id)
    if module is None:
        return {}
    module_def = session.get(ModuleDefinition, module.module_def_id)
    process = session.get(ProcessInstance, module.process_instance_id)
    ctx: dict[str, str] = {}
    if process is not None:
        ctx["Kundenname"] = process.customer_name or ""
        ctx["Organisation"] = process.customer_org or ""
    if module_def is not None:
        ctx["Modulname"] = module_def.name or ""
    return ctx


def render(text: str | None, context: dict[str, str]) -> str | None:
    if text is None:
        return None

    def _sub(match: re.Match) -> str:
        key = match.group(1)
        return context.get(key, match.group(0))

    return _PLACEHOLDER_RE.sub(_sub, text)


def render_template(
    template: TemplateDefinition, context: dict[str, str]
) -> dict:
    """Return a dict mirroring the OpenAPI ``Template`` schema (rendered)."""
    return {
        "key": template.key,
        "type": template.type,
        "title": template.title,
        "subject": render(template.subject, context),
        "body": render(template.body, context),
        "file_name": template.file_name,
        "file_type": template.file_type,
    }
