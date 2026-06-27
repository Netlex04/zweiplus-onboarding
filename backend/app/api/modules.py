"""Modules router: GET /api/modules/{moduleInstanceId}."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import assert_module_access, get_module_or_404
from app.auth import current_user
from app.db.session import get_session
from app.models import User
from app.schemas import ModuleDetail
from app.services import dto

router = APIRouter(prefix="/api/modules", tags=["module"])


@router.get("/{module_instance_id}", response_model=ModuleDetail)
def get_module(
    module_instance_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> ModuleDetail:
    module = get_module_or_404(session, module_instance_id)
    assert_module_access(session, user, module)
    return ModuleDetail.model_validate(dto.module_detail(session, module))
