"""Review router (reviewer/admin only): tasks, review view, edit, approve.

Customer access is rejected with 403 (``require_role``). FR-REV-001..003.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_module_or_404
from app.auth import require_role
from app.db.session import get_session
from app.models import Answer, ModuleInstance, StepInstance, User
from app.models.enums import AnswerSource, Role
from app.schemas import (
    AnswerOut,
    ModuleDetail,
    PatchAnswerRequest,
    RequestChangesRequest,
    ReviewTaskOut,
    ReviewView,
)
from app.services import dto, review_service, validation
from app.services.module_engine import question_def_by_step

router = APIRouter(prefix="/api/review", tags=["review"])

# Reviewer + admin may use every review endpoint; customers get 403.
_reviewer = require_role(Role.REVIEWER, Role.ADMIN)


@router.get("/tasks", response_model=list[ReviewTaskOut])
def list_tasks(
    session: Session = Depends(get_session),
    user: User = Depends(_reviewer),
) -> list[ReviewTaskOut]:
    tasks = review_service.list_open_tasks(session)
    session.commit()
    return [ReviewTaskOut.model_validate(t) for t in tasks]


@router.get("/modules/{module_instance_id}", response_model=ReviewView)
def get_review_view(
    module_instance_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(_reviewer),
) -> ReviewView:
    module = get_module_or_404(session, module_instance_id)
    view = review_service.review_view(session, module)
    return ReviewView.model_validate(view)


@router.patch("/answers/{answer_id}", response_model=AnswerOut)
def patch_answer(
    answer_id: str,
    payload: PatchAnswerRequest,
    session: Session = Depends(get_session),
    user: User = Depends(_reviewer),
) -> AnswerOut:
    answer = session.get(Answer, answer_id)
    if answer is None:
        raise HTTPException(status_code=404, detail="Antwort nicht gefunden")

    answer.value = payload.value
    answer.source = AnswerSource.MANUAL.value
    answer.created_by = user.email
    session.flush()

    # Re-validate the owning step so backend validation reflects the edit.
    step = session.get(StepInstance, answer.step_instance_id)
    if step is not None:
        validation.run_step_validation(session, step)
    qkey = next(
        (
            q.key
            for q in question_def_by_step(session, step.step_def_id)
            if q.id == answer.question_def_id
        ),
        "",
    )
    session.commit()
    session.refresh(answer)
    return AnswerOut.model_validate(
        {
            "id": answer.id,
            "question_key": qkey,
            "value": answer.value,
            "source": answer.source,
            "ai_suggested": answer.ai_suggested,
            "updated_at": answer.updated_at,
        }
    )


@router.post("/modules/{module_instance_id}/approve", response_model=ModuleDetail)
def approve_module(
    module_instance_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(_reviewer),
) -> ModuleDetail:
    module = get_module_or_404(session, module_instance_id)
    try:
        review_service.approve(session, module, reviewer=user.email)
    except review_service.ReviewNotAllowed as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    session.commit()
    session.refresh(module)
    return ModuleDetail.model_validate(dto.module_detail(session, module))


@router.post(
    "/modules/{module_instance_id}/request-changes", response_model=ModuleDetail
)
def request_changes(
    module_instance_id: str,
    payload: RequestChangesRequest | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(_reviewer),
) -> ModuleDetail:
    module = get_module_or_404(session, module_instance_id)
    notes = payload.notes if payload else None
    try:
        review_service.request_changes(
            session, module, reviewer=user.email, notes=notes
        )
    except review_service.ReviewNotAllowed as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    session.commit()
    session.refresh(module)
    return ModuleDetail.model_validate(dto.module_detail(session, module))
