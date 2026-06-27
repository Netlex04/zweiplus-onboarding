"""Shared API helpers: ownership / access checks."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import ModuleInstance, ProcessInstance, StepInstance, User
from app.models.enums import Role


def _is_staff(user: User) -> bool:
    return user.role in (Role.REVIEWER.value, Role.ADMIN.value)


def assert_process_access(user: User, process: ProcessInstance) -> None:
    """Reviewer/admin may access any process; a customer only their own.

    Ownership for a customer is matched on ``customer_name == user.name``
    (MVP convention; no User<->Process FK exists, see Architektur §12).
    """
    if _is_staff(user):
        return
    if process.customer_name and user.name and process.customer_name == user.name:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Kein Zugriff auf diesen Prozess",
    )


def get_process_or_404(session: Session, process_id: str) -> ProcessInstance:
    process = session.get(ProcessInstance, process_id)
    if process is None:
        raise HTTPException(status_code=404, detail="Prozess nicht gefunden")
    return process


def get_module_or_404(session: Session, module_instance_id: str) -> ModuleInstance:
    module = session.get(ModuleInstance, module_instance_id)
    if module is None:
        raise HTTPException(status_code=404, detail="Modul nicht gefunden")
    return module


def get_step_or_404(session: Session, step_instance_id: str) -> StepInstance:
    step = session.get(StepInstance, step_instance_id)
    if step is None:
        raise HTTPException(status_code=404, detail="Step nicht gefunden")
    return step


def assert_module_access(session: Session, user: User, module: ModuleInstance) -> None:
    process = session.get(ProcessInstance, module.process_instance_id)
    assert_process_access(user, process)


def assert_step_access(session: Session, user: User, step: StepInstance) -> None:
    module = session.get(ModuleInstance, step.module_instance_id)
    assert_module_access(session, user, module)
