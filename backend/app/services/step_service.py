"""Step mutation logic: save answers, run validation, drive the state machine.

Separated from the API router so it is unit-testable. Phases 3/4 may reuse
``save_answers`` / ``complete_step``.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Answer,
    ModuleDefinition,
    ModuleInstance,
    ProcessInstance,
    QuestionDefinition,
    StepDefinition,
    StepInstance,
)
from app.models.enums import AnswerSource, ModuleStatus, StepStatus
from app.services import module_engine, validation
from app.services.statemachine import (
    assert_step_transition,
    module_can_transition,
)


class StepNotEditable(Exception):
    """Raised when answers are saved on a step that cannot transition."""


def _question_map(session: Session, step_def_id: str) -> dict[str, QuestionDefinition]:
    questions = module_engine.question_def_by_step(session, step_def_id)
    return {q.key: q for q in questions}


def _set_step_status(step: StepInstance, target: StepStatus) -> None:
    assert_step_transition(step.status, target)
    step.status = target.value


def _mark_module_in_progress(session: Session, step: StepInstance) -> None:
    module = session.get(ModuleInstance, step.module_instance_id)
    if module is None:
        return
    if module.status in (
        ModuleStatus.AVAILABLE.value,
        ModuleStatus.NOT_STARTED.value,
    ):
        module.status = ModuleStatus.IN_PROGRESS.value


def save_answers(
    session: Session,
    step: StepInstance,
    answers: list[dict],
    *,
    created_by: str | None,
    source: AnswerSource = AnswerSource.USER,
) -> validation.ValidationOutcome:
    """Upsert answers, run backend validation, set step status. Returns outcome.

    ``answers`` is a list of ``{"question_key": ..., "value": ...}``.
    """
    step_def = session.get(StepDefinition, step.step_def_id)
    qmap = _question_map(session, step_def.id)

    # Move the step into in_progress on first edit (if currently not_started).
    if step.status == StepStatus.NOT_STARTED.value:
        _set_step_status(step, StepStatus.IN_PROGRESS)
    elif step.status in (
        StepStatus.COMPLETE.value,
        StepStatus.COMPLETED.value,
        StepStatus.REVIEW_PENDING.value,
    ):
        # Re-editing a finished step reopens it.
        _set_step_status(step, StepStatus.IN_PROGRESS)

    _mark_module_in_progress(session, step)

    existing = {a.question_def_id: a for a in step.answers}
    for item in answers:
        qkey = item.get("question_key")
        question = qmap.get(qkey)
        if question is None:
            continue  # ignore unknown keys; validation covers required fields
        value = item.get("value")
        ans = existing.get(question.id)
        if ans is None:
            ans = Answer(
                step_instance_id=step.id,
                question_def_id=question.id,
                value=value,
                source=source.value,
                created_by=created_by,
            )
            session.add(ans)
            existing[question.id] = ans
        else:
            ans.value = value
            ans.source = source.value
            ans.created_by = created_by
    session.flush()
    session.refresh(step)

    outcome, _ = validation.run_step_validation(session, step)

    # Status reflects validation result while editing (not auto-complete).
    if not outcome.passed:
        _set_step_status(step, StepStatus.BACKEND_VALIDATION_FAILED)
    else:
        # Valid but not yet explicitly completed -> remain/return to in_progress.
        if step.status == StepStatus.BACKEND_VALIDATION_FAILED.value:
            _set_step_status(step, StepStatus.IN_PROGRESS)
    session.flush()
    return outcome


def complete_step(
    session: Session, step: StepInstance
) -> validation.ValidationOutcome:
    """Validate and, only if valid, transition the step to ``complete``.

    Raises ``StepNotEditable`` (mapped to 409) when validation fails.
    On success, recomputes module status/unlocks.
    """
    # A complete request implies the step is being worked on; ensure it has
    # left not_started so the failure status is a legal transition.
    if step.status == StepStatus.NOT_STARTED.value:
        _set_step_status(step, StepStatus.IN_PROGRESS)

    outcome = validation.validate_step(session, step)
    if not outcome.passed:
        _set_step_status(step, StepStatus.BACKEND_VALIDATION_FAILED)
        session.flush()
        raise StepNotEditable("Step ist nicht valide und kann nicht abgeschlossen werden")

    _set_step_status(step, StepStatus.COMPLETE)
    session.flush()
    _advance_module_after_step(session, step)
    session.flush()
    return outcome


def _advance_module_after_step(session: Session, step: StepInstance) -> None:
    module = session.get(ModuleInstance, step.module_instance_id)
    if module is None:
        return
    all_done = all(
        s.status in (StepStatus.COMPLETE.value, StepStatus.COMPLETED.value)
        for s in module.steps
    )
    if all_done and module.status not in (
        ModuleStatus.WAITING_ZWEIPLUS.value,
        ModuleStatus.COMPLETED.value,
        ModuleStatus.IMPORT_READY.value,
        ModuleStatus.IMPORTED.value,
    ):
        if module_can_transition(module.status, ModuleStatus.WAITING_ZWEIPLUS.value):
            module.status = ModuleStatus.WAITING_ZWEIPLUS.value
    # Re-evaluate follow-up module unlocks (software_inventory -> tom/avv).
    process = session.get(ProcessInstance, module.process_instance_id)
    if process is not None:
        module_engine.evaluate_unlocks(session, process)
