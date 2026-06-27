"""Processes router: create, list (staff), dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import assert_process_access, get_process_or_404
from app.auth import current_user, require_role
from app.db.session import get_session
from app.models import ProcessInstance, User
from app.models.enums import Role
from app.schemas import CreateProcessRequest, Dashboard, ProcessSummary
from app.services import dto, module_engine

router = APIRouter(prefix="/api/processes", tags=["process"])


@router.post("", response_model=Dashboard, status_code=201)
def create_process(
    payload: CreateProcessRequest,
    session: Session = Depends(get_session),
    _user: User = Depends(current_user),
) -> Dashboard:
    try:
        process = module_engine.create_process_instance(
            session,
            process_def_key=payload.process_def_key,
            customer_name=payload.customer_name,
            customer_org=payload.customer_org,
        )
    except module_engine.ProcessDefinitionNotFound:
        raise HTTPException(status_code=404, detail="Prozessdefinition nicht gefunden")
    session.commit()
    session.refresh(process)
    return Dashboard.model_validate(dto.dashboard(session, process))


@router.get("", response_model=list[ProcessSummary])
def list_processes(
    session: Session = Depends(get_session),
    _user: User = Depends(require_role(Role.REVIEWER, Role.ADMIN)),
) -> list[ProcessSummary]:
    processes = session.scalars(select(ProcessInstance)).all()
    return [
        ProcessSummary(
            id=p.id,
            customer_name=p.customer_name,
            customer_org=p.customer_org,
            status=p.status,
        )
        for p in processes
    ]


@router.get("/{process_id}", response_model=Dashboard)
def get_dashboard(
    process_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> Dashboard:
    process = get_process_or_404(session, process_id)
    assert_process_access(user, process)
    return Dashboard.model_validate(dto.dashboard(session, process))
