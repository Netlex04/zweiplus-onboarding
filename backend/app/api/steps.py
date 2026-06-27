"""Steps router: detail, save answers (+validate), complete."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import assert_step_access, get_step_or_404
from app.auth import current_user
from app.db.session import get_session
from app.models import User
from app.schemas import (
    BackendValidationResultOut,
    PutAnswersRequest,
    PutAnswersResponse,
    StepDetail,
)
from app.services import dto, step_service

router = APIRouter(prefix="/api/steps", tags=["step"])


@router.get("/{step_instance_id}", response_model=StepDetail)
def get_step(
    step_instance_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> StepDetail:
    step = get_step_or_404(session, step_instance_id)
    assert_step_access(session, user, step)
    return StepDetail.model_validate(dto.step_detail(session, step))


@router.put("/{step_instance_id}/answers", response_model=PutAnswersResponse)
def put_answers(
    step_instance_id: str,
    payload: PutAnswersRequest,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> PutAnswersResponse:
    step = get_step_or_404(session, step_instance_id)
    assert_step_access(session, user, step)
    answers = [
        {"question_key": a.question_key, "value": a.value} for a in payload.answers
    ]
    outcome = step_service.save_answers(
        session, step, answers, created_by=user.email
    )
    session.commit()
    session.refresh(step)
    return PutAnswersResponse(
        step_status=step.status,
        validation=BackendValidationResultOut(
            passed=outcome.passed,
            errors=outcome.errors,
            warnings=outcome.warnings,
        ),
    )


@router.post("/{step_instance_id}/complete", response_model=StepDetail)
def complete_step(
    step_instance_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> StepDetail:
    step = get_step_or_404(session, step_instance_id)
    assert_step_access(session, user, step)
    try:
        step_service.complete_step(session, step)
    except step_service.StepNotEditable as exc:
        session.commit()  # persist the failed-validation status
        raise HTTPException(status_code=409, detail=str(exc))
    session.commit()
    session.refresh(step)
    return StepDetail.model_validate(dto.step_detail(session, step))
