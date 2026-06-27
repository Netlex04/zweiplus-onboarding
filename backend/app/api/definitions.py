"""Definitions router: GET /api/process-definitions."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db.session import get_session
from app.models import ModuleDefinition, ProcessDefinition, User
from app.schemas import ModuleDefinitionSummary, ProcessDefinitionOut

router = APIRouter(prefix="/api/process-definitions", tags=["definitions"])


@router.get("", response_model=list[ProcessDefinitionOut])
def list_process_definitions(
    session: Session = Depends(get_session),
    _user: User = Depends(current_user),
) -> list[ProcessDefinitionOut]:
    processes = session.scalars(select(ProcessDefinition)).all()
    result: list[ProcessDefinitionOut] = []
    for proc in processes:
        modules = sorted(
            (m for m in proc.modules if m.enabled),
            key=lambda m: (m.order_index, m.key),
        )
        result.append(
            ProcessDefinitionOut(
                key=proc.key,
                name=proc.name,
                description=proc.description,
                modules=[
                    ModuleDefinitionSummary(
                        key=m.key,
                        name=m.name,
                        short_description=m.short_description,
                        responsible_role=m.responsible_role,
                        estimated_effort=m.estimated_effort,
                    )
                    for m in modules
                ],
            )
        )
    return result
