"""Deterministic status state machines (Architektur §5.3).

Single source of truth for which status transitions are legal on
``StepInstance`` and ``ModuleInstance``. Illegal transitions raise
``IllegalTransition`` so the API can reject them deterministically.

The allowed-transition maps are intentionally permissive enough to support the
Phase 2 flow (answer → in_progress → complete) while rejecting nonsensical
jumps. Later phases (review/import) consume the same machine for their stages.
"""

from __future__ import annotations

from app.models.enums import ImportStatus, ModuleStatus, StepStatus


class IllegalTransition(Exception):
    """Raised when a requested status transition is not allowed."""

    def __init__(self, current: str, target: str, kind: str) -> None:
        self.current = current
        self.target = target
        self.kind = kind
        super().__init__(
            f"Illegal {kind} transition: {current} -> {target}"
        )


# StepInstance: not_started -> in_progress -> (incomplete | ai_check_pending |
# backend_validation_failed) -> complete -> review_pending -> completed
_STEP_TRANSITIONS: dict[StepStatus, set[StepStatus]] = {
    StepStatus.NOT_STARTED: {
        StepStatus.IN_PROGRESS,
    },
    StepStatus.IN_PROGRESS: {
        StepStatus.IN_PROGRESS,
        StepStatus.INCOMPLETE,
        StepStatus.AI_CHECK_PENDING,
        StepStatus.BACKEND_VALIDATION_FAILED,
        StepStatus.COMPLETE,
    },
    StepStatus.INCOMPLETE: {
        StepStatus.IN_PROGRESS,
        StepStatus.INCOMPLETE,
        StepStatus.AI_CHECK_PENDING,
        StepStatus.BACKEND_VALIDATION_FAILED,
        StepStatus.COMPLETE,
    },
    StepStatus.AI_CHECK_PENDING: {
        StepStatus.IN_PROGRESS,
        StepStatus.INCOMPLETE,
        StepStatus.BACKEND_VALIDATION_FAILED,
        StepStatus.COMPLETE,
    },
    StepStatus.BACKEND_VALIDATION_FAILED: {
        StepStatus.IN_PROGRESS,
        StepStatus.INCOMPLETE,
        StepStatus.AI_CHECK_PENDING,
        StepStatus.BACKEND_VALIDATION_FAILED,
        StepStatus.COMPLETE,
    },
    StepStatus.COMPLETE: {
        # Re-editing a complete step drops back to in_progress;
        # review advances it forward.
        StepStatus.IN_PROGRESS,
        StepStatus.BACKEND_VALIDATION_FAILED,
        StepStatus.REVIEW_PENDING,
        StepStatus.COMPLETED,
    },
    StepStatus.REVIEW_PENDING: {
        StepStatus.IN_PROGRESS,
        StepStatus.COMPLETE,
        StepStatus.COMPLETED,
    },
    StepStatus.COMPLETED: {
        StepStatus.IN_PROGRESS,
    },
}


# ModuleInstance: locked | available | not_started | in_progress |
# waiting_customer | waiting_zweiplus | ai_check_pending |
# backend_validation_failed | completed | import_ready | imported
_MODULE_TRANSITIONS: dict[ModuleStatus, set[ModuleStatus]] = {
    ModuleStatus.LOCKED: {
        ModuleStatus.AVAILABLE,
    },
    ModuleStatus.AVAILABLE: {
        ModuleStatus.LOCKED,
        ModuleStatus.NOT_STARTED,
        ModuleStatus.IN_PROGRESS,
    },
    ModuleStatus.NOT_STARTED: {
        ModuleStatus.IN_PROGRESS,
        ModuleStatus.AVAILABLE,
    },
    ModuleStatus.IN_PROGRESS: {
        ModuleStatus.IN_PROGRESS,
        ModuleStatus.WAITING_CUSTOMER,
        ModuleStatus.WAITING_ZWEIPLUS,
        ModuleStatus.AI_CHECK_PENDING,
        ModuleStatus.BACKEND_VALIDATION_FAILED,
    },
    ModuleStatus.WAITING_CUSTOMER: {
        ModuleStatus.IN_PROGRESS,
        ModuleStatus.WAITING_ZWEIPLUS,
    },
    ModuleStatus.WAITING_ZWEIPLUS: {
        ModuleStatus.IN_PROGRESS,
        ModuleStatus.BACKEND_VALIDATION_FAILED,
        ModuleStatus.COMPLETED,
    },
    ModuleStatus.AI_CHECK_PENDING: {
        ModuleStatus.IN_PROGRESS,
        ModuleStatus.WAITING_ZWEIPLUS,
        ModuleStatus.BACKEND_VALIDATION_FAILED,
    },
    ModuleStatus.BACKEND_VALIDATION_FAILED: {
        ModuleStatus.IN_PROGRESS,
        ModuleStatus.WAITING_ZWEIPLUS,
    },
    ModuleStatus.COMPLETED: {
        ModuleStatus.IN_PROGRESS,
        ModuleStatus.IMPORT_READY,
    },
    ModuleStatus.IMPORT_READY: {
        ModuleStatus.IMPORTED,
        ModuleStatus.COMPLETED,
    },
    ModuleStatus.IMPORTED: set(),
}


# ImportJob (Architektur §5.3, FR-INT-005):
# not_prepared -> mapping_ready -> validated -> approved -> importing ->
# (imported | import_failed). import_failed / reimport_required re-enter the
# pipeline at mapping_ready.
_IMPORT_TRANSITIONS: dict[ImportStatus, set[ImportStatus]] = {
    ImportStatus.NOT_PREPARED: {
        ImportStatus.MAPPING_READY,
    },
    ImportStatus.MAPPING_READY: {
        ImportStatus.VALIDATED,
        ImportStatus.IMPORT_FAILED,
    },
    ImportStatus.VALIDATED: {
        ImportStatus.APPROVED,
        ImportStatus.MAPPING_READY,
        ImportStatus.IMPORT_FAILED,
    },
    ImportStatus.APPROVED: {
        ImportStatus.IMPORTING,
        ImportStatus.IMPORT_FAILED,
    },
    ImportStatus.IMPORTING: {
        ImportStatus.IMPORTED,
        ImportStatus.IMPORT_FAILED,
    },
    ImportStatus.IMPORTED: {
        ImportStatus.REIMPORT_REQUIRED,
    },
    ImportStatus.IMPORT_FAILED: {
        ImportStatus.MAPPING_READY,
        ImportStatus.REIMPORT_REQUIRED,
    },
    ImportStatus.REIMPORT_REQUIRED: {
        ImportStatus.MAPPING_READY,
    },
}


def _coerce(value: object, enum_cls):
    if isinstance(value, enum_cls):
        return value
    return enum_cls(value)


def step_can_transition(current: object, target: object) -> bool:
    current = _coerce(current, StepStatus)
    target = _coerce(target, StepStatus)
    if current == target:
        return True
    return target in _STEP_TRANSITIONS.get(current, set())


def module_can_transition(current: object, target: object) -> bool:
    current = _coerce(current, ModuleStatus)
    target = _coerce(target, ModuleStatus)
    if current == target:
        return True
    return target in _MODULE_TRANSITIONS.get(current, set())


def import_can_transition(current: object, target: object) -> bool:
    current = _coerce(current, ImportStatus)
    target = _coerce(target, ImportStatus)
    if current == target:
        return True
    return target in _IMPORT_TRANSITIONS.get(current, set())


def assert_import_transition(current: object, target: object) -> None:
    if not import_can_transition(current, target):
        raise IllegalTransition(str(_coerce(current, ImportStatus).value),
                                str(_coerce(target, ImportStatus).value), "import")


def assert_step_transition(current: object, target: object) -> None:
    if not step_can_transition(current, target):
        raise IllegalTransition(str(_coerce(current, StepStatus).value),
                                str(_coerce(target, StepStatus).value), "step")


def assert_module_transition(current: object, target: object) -> None:
    if not module_can_transition(current, target):
        raise IllegalTransition(str(_coerce(current, ModuleStatus).value),
                                str(_coerce(target, ModuleStatus).value), "module")
