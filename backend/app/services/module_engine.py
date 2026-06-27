"""Module engine: instance creation, unlock evaluation, progress (Architektur §5.3).

Pure-ish service functions operating on a SQLAlchemy ``Session``. No HTTP here —
the API layer (Phase 2) and later phases call into this module.

Responsibilities:
- ``create_process_instance`` — materialise ProcessInstance + ModuleInstances +
  StepInstances from the seeded definitions and set initial unlock/status.
- ``evaluate_unlocks`` — (re)compute ``unlocked``/status for all modules of a
  process from each module's ``unlock_rule`` and the completion of its
  prerequisites. Called after module completion to open follow-up modules.
- ``module_progress`` — completed steps / total steps as 0-100 percent.
- ``is_question_visible`` — visibility_rule evaluation against current answers
  (FR-Q-007).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Answer,
    ModuleDefinition,
    ModuleInstance,
    ProcessDefinition,
    ProcessInstance,
    QuestionDefinition,
    StepDefinition,
    StepInstance,
)
from app.models.enums import ModuleStatus, StepStatus
from app.services.statemachine import assert_module_transition

# Step statuses that count as "done" for progress (Architektur §5.3).
_DONE_STEP_STATUSES = {StepStatus.COMPLETE.value, StepStatus.COMPLETED.value}


class ProcessDefinitionNotFound(Exception):
    pass


def create_process_instance(
    session: Session,
    *,
    process_def_key: str,
    customer_name: str | None,
    customer_org: str | None = None,
) -> ProcessInstance:
    """Create a ProcessInstance and all Module/Step instances; set initial unlocks."""
    process_def = session.scalar(
        select(ProcessDefinition).where(ProcessDefinition.key == process_def_key)
    )
    if process_def is None:
        raise ProcessDefinitionNotFound(process_def_key)

    process = ProcessInstance(
        process_def_id=process_def.id,
        customer_name=customer_name,
        customer_org=customer_org,
    )
    session.add(process)
    session.flush()

    module_defs = sorted(
        (m for m in process_def.modules if m.enabled),
        key=lambda m: (m.order_index, m.key),
    )
    for module_def in module_defs:
        module = ModuleInstance(
            process_instance_id=process.id,
            module_def_id=module_def.id,
            status=ModuleStatus.LOCKED.value,
            unlocked=False,
            assigned_role=module_def.responsible_role,
        )
        session.add(module)
        session.flush()

        step_defs = sorted(
            module_def.steps, key=lambda s: (s.order_index, s.key)
        )
        for step_def in step_defs:
            session.add(
                StepInstance(
                    module_instance_id=module.id,
                    step_def_id=step_def.id,
                    status=StepStatus.NOT_STARTED.value,
                )
            )
    session.flush()

    evaluate_unlocks(session, process)
    session.flush()
    return process


def _module_completed(module: ModuleInstance) -> bool:
    return module.status in {
        ModuleStatus.COMPLETED.value,
        ModuleStatus.IMPORT_READY.value,
        ModuleStatus.IMPORTED.value,
        ModuleStatus.WAITING_ZWEIPLUS.value,
    }


def _all_steps_done(module: ModuleInstance) -> bool:
    steps = module.steps
    if not steps:
        return False
    return all(s.status in _DONE_STEP_STATUSES for s in steps)


def evaluate_unlocks(session: Session, process: ProcessInstance) -> None:
    """Recompute unlock state for every module of ``process``.

    A module with ``unlock_rule.type == "always"`` is always unlocked.
    ``"after"`` is unlocked once every required module (by key) has all its
    steps done. ``"manual"`` stays locked until opened explicitly.

    Locked->available and available->locked transitions are applied; modules
    that are already in progress / further along are left untouched.
    """
    modules = list(process.modules)
    # Map module-definition-key -> "is its prerequisite satisfied (steps done)".
    def_by_module_id = {
        m.id: session.get(ModuleDefinition, m.module_def_id) for m in modules
    }
    done_keys: set[str] = set()
    for module in modules:
        mdef = def_by_module_id[module.id]
        if mdef and (_module_completed(module) or _all_steps_done(module)):
            done_keys.add(mdef.key)

    for module in modules:
        mdef = def_by_module_id[module.id]
        rule = (mdef.unlock_rule if mdef else None) or {"type": "manual"}
        unlocked = _is_unlocked(rule, done_keys)
        _apply_unlock(module, unlocked)


def _is_unlocked(rule: dict, done_keys: set[str]) -> bool:
    rule_type = rule.get("type")
    if rule_type == "always":
        return True
    if rule_type == "after":
        requires = rule.get("requires", []) or []
        return all(req in done_keys for req in requires)
    # "manual" or unknown -> not auto-unlocked
    return False


def _apply_unlock(module: ModuleInstance, unlocked: bool) -> None:
    if unlocked:
        module.unlocked = True
        if module.status == ModuleStatus.LOCKED.value:
            assert_module_transition(module.status, ModuleStatus.AVAILABLE)
            module.status = ModuleStatus.AVAILABLE.value
    else:
        module.unlocked = False
        if module.status == ModuleStatus.AVAILABLE.value:
            module.status = ModuleStatus.LOCKED.value


def module_progress(module: ModuleInstance) -> int:
    """Completed steps / total steps as an integer percentage (0-100)."""
    steps = module.steps
    if not steps:
        return 0
    done = sum(1 for s in steps if s.status in _DONE_STEP_STATUSES)
    return round(done * 100 / len(steps))


def overall_progress(process: ProcessInstance) -> int:
    """Average module progress weighted by step count across the process."""
    total = 0
    done = 0
    for module in process.modules:
        steps = module.steps
        total += len(steps)
        done += sum(1 for s in steps if s.status in _DONE_STEP_STATUSES)
    if total == 0:
        return 0
    return round(done * 100 / total)


def unlock_hint(module_def: ModuleDefinition) -> str | None:
    """Human-readable hint describing what unlocks a locked module."""
    rule = module_def.unlock_rule or {}
    if rule.get("type") == "after":
        requires = rule.get("requires", []) or []
        if requires:
            return "Wird freigeschaltet nach Abschluss von: " + ", ".join(requires)
    if rule.get("type") == "manual":
        return "Wird durch Zweiplus manuell freigeschaltet."
    return None


def is_question_visible(
    question: QuestionDefinition, answers_by_key: dict[str, object]
) -> bool:
    """Evaluate ``visibility_rule`` against current answers (FR-Q-007).

    Rule form: ``{"questionKey": "...", "equals": "..."}`` — visible only when
    the referenced answer equals the given value. ``None`` => always visible.
    """
    rule = question.visibility_rule
    if not rule:
        return True
    ref_key = rule.get("questionKey")
    expected = rule.get("equals")
    actual = answers_by_key.get(ref_key)
    return actual == expected


def question_def_by_step(session: Session, step_def_id: str) -> list[QuestionDefinition]:
    return list(
        session.scalars(
            select(QuestionDefinition)
            .where(QuestionDefinition.step_def_id == step_def_id)
            .order_by(QuestionDefinition.order_index, QuestionDefinition.key)
        )
    )


def answers_by_question_key(
    session: Session, step_instance: StepInstance
) -> dict[str, object]:
    """Map question key -> stored answer value for a step instance."""
    step_def = session.get(StepDefinition, step_instance.step_def_id)
    questions = question_def_by_step(session, step_def.id)
    qid_to_key = {q.id: q.key for q in questions}
    result: dict[str, object] = {}
    for ans in step_instance.answers:
        key = qid_to_key.get(ans.question_def_id)
        if key is not None:
            result[key] = ans.value
    return result
