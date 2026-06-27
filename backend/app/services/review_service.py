"""Review service (FR-REV-001..003): tasks, review view, approve/request-changes.

Keeps the review router thin. Manages ``ReviewTask`` lifecycle and assembles the
``ReviewView`` (answers incl. provenance, AI suggestions, AI + backend
validation) from the existing instance data.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AiSuggestion,
    AiValidationResult,
    BackendValidationResult,
    ModuleDefinition,
    ModuleInstance,
    ProcessInstance,
    ReviewTask,
    StepDefinition,
    StepInstance,
)
from app.models.enums import ModuleStatus, ReviewStatus
from app.services import module_engine
from app.services.statemachine import assert_module_transition

# Module statuses that warrant an open review task.
_REVIEW_STATES = {ModuleStatus.WAITING_ZWEIPLUS.value}


class ReviewNotAllowed(Exception):
    """Raised when approve/request-changes is invoked from an invalid state."""


def get_or_create_task(session: Session, module: ModuleInstance) -> ReviewTask:
    """Return the module's ReviewTask, creating an ``open`` one if missing."""
    task = session.scalar(
        select(ReviewTask).where(ReviewTask.module_instance_id == module.id)
    )
    if task is None:
        task = ReviewTask(
            module_instance_id=module.id, status=ReviewStatus.OPEN.value
        )
        session.add(task)
        session.flush()
    return task


def _customer_name(session: Session, module: ModuleInstance) -> str | None:
    process = session.get(ProcessInstance, module.process_instance_id)
    return process.customer_name if process else None


def _task_dto(session: Session, task: ReviewTask) -> dict:
    module = session.get(ModuleInstance, task.module_instance_id)
    mdef = session.get(ModuleDefinition, module.module_def_id) if module else None
    return {
        "id": task.id,
        "module_instance_id": task.module_instance_id,
        "customer_name": _customer_name(session, module) if module else None,
        "module_name": mdef.name if mdef else "",
        "status": task.status,
        "notes": task.notes,
    }


def list_open_tasks(session: Session) -> list[dict]:
    """Open review tasks: modules awaiting review (waiting_zweiplus) + any task
    that is not yet ``approved``. Lazily materialises a task for modules in a
    review state that have none yet.
    """
    # Ensure a task exists for every module currently awaiting review.
    waiting = session.scalars(
        select(ModuleInstance).where(ModuleInstance.status.in_(_REVIEW_STATES))
    ).all()
    for module in waiting:
        get_or_create_task(session, module)
    session.flush()

    tasks = session.scalars(
        select(ReviewTask).where(ReviewTask.status != ReviewStatus.APPROVED.value)
    ).all()
    return [_task_dto(session, t) for t in tasks]


def _latest(rows: list, key=lambda r: r.created_at):
    return max(rows, key=key) if rows else None


def review_view(session: Session, module: ModuleInstance) -> dict:
    """Assemble the ReviewView for a module (steps -> questions -> provenance)."""
    mdef = session.get(ModuleDefinition, module.module_def_id)
    steps = sorted(
        module.steps,
        key=lambda s: session.get(StepDefinition, s.step_def_id).order_index,
    )

    step_dtos: list[dict] = []
    for step in steps:
        sdef = session.get(StepDefinition, step.step_def_id)
        questions = module_engine.question_def_by_step(session, sdef.id)
        answers_by_key = module_engine.answers_by_question_key(session, step)
        answer_rows = {a.question_def_id: a for a in step.answers}

        # AI suggestions for this step, grouped by question id.
        suggestions = session.scalars(
            select(AiSuggestion).where(
                AiSuggestion.step_instance_id == step.id
            )
        ).all()
        sugg_by_qid: dict[str | None, list[AiSuggestion]] = {}
        for s in suggestions:
            sugg_by_qid.setdefault(s.question_def_id, []).append(s)

        question_dtos = []
        for q in questions:
            ans = answer_rows.get(q.id)
            question_dtos.append(
                {
                    "key": q.key,
                    "label": q.label,
                    "answer": _answer_dto(ans, q.key) if ans else None,
                    "ai_suggestions": [
                        _suggestion_dto(s) for s in sugg_by_qid.get(q.id, [])
                    ],
                }
            )

        ai_val = _latest(
            session.scalars(
                select(AiValidationResult).where(
                    AiValidationResult.step_instance_id == step.id
                )
            ).all()
        )
        be_val = _latest(
            session.scalars(
                select(BackendValidationResult).where(
                    BackendValidationResult.step_instance_id == step.id
                )
            ).all()
        )

        step_dtos.append(
            {
                "step_instance_id": step.id,
                "title": sdef.title,
                "questions": question_dtos,
                "ai_validation": _ai_validation_dto(ai_val) if ai_val else None,
                "backend_validation": (
                    _backend_validation_dto(be_val) if be_val else None
                ),
            }
        )

    task = session.scalar(
        select(ReviewTask).where(ReviewTask.module_instance_id == module.id)
    )
    return {
        "module_instance_id": module.id,
        "module_name": mdef.name if mdef else "",
        "module_status": module.status,
        "customer_name": _customer_name(session, module),
        "review_status": task.status if task else None,
        "steps": step_dtos,
    }


def approve(session: Session, module: ModuleInstance, reviewer: str | None) -> None:
    """Approve a module: transition to ``completed`` + task ``approved``."""
    try:
        assert_module_transition(module.status, ModuleStatus.COMPLETED)
    except Exception as exc:  # IllegalTransition
        raise ReviewNotAllowed(str(exc)) from exc
    module.status = ModuleStatus.COMPLETED.value
    task = get_or_create_task(session, module)
    task.status = ReviewStatus.APPROVED.value
    task.reviewer = reviewer
    session.flush()


def request_changes(
    session: Session,
    module: ModuleInstance,
    reviewer: str | None,
    notes: str | None,
) -> None:
    """Return a module to the customer: ``in_progress`` + task changes_requested."""
    try:
        assert_module_transition(module.status, ModuleStatus.IN_PROGRESS)
    except Exception as exc:  # IllegalTransition
        raise ReviewNotAllowed(str(exc)) from exc
    module.status = ModuleStatus.IN_PROGRESS.value
    task = get_or_create_task(session, module)
    task.status = ReviewStatus.CHANGES_REQUESTED.value
    task.reviewer = reviewer
    task.notes = notes
    session.flush()


# --- DTO helpers (mirror the OpenAPI nested schemas) ----------------------


def _answer_dto(answer, question_key: str) -> dict:
    return {
        "id": answer.id,
        "question_key": question_key,
        "value": answer.value,
        "source": answer.source,
        "ai_suggested": answer.ai_suggested,
        "updated_at": answer.updated_at,
    }


def _suggestion_dto(s: AiSuggestion) -> dict:
    payload = s.payload or {}
    return {
        "id": s.id,
        "suggestion_type": s.suggestion_type,
        "module_id": s.module_instance_id,
        "step_id": s.step_instance_id,
        "question_id": s.question_def_id,
        "proposed_value": payload.get("proposedValue"),
        "confidence": s.confidence,
        "requires_review": s.requires_review,
        "open_questions": s.open_questions or [],
        "source_upload_id": s.source_upload_id,
    }


def _ai_validation_dto(v: AiValidationResult) -> dict:
    return {
        "id": v.id,
        "passed": v.passed,
        "checks": v.checks or [],
        "issues": v.issues or [],
    }


def _backend_validation_dto(v: BackendValidationResult) -> dict:
    return {
        "passed": v.passed,
        "errors": v.errors or [],
        "warnings": v.warnings or [],
    }
