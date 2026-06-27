"""State machine: allowed vs illegal transitions (Architektur §5.3)."""

import pytest

from app.models.enums import ModuleStatus, StepStatus
from app.services.statemachine import (
    IllegalTransition,
    assert_module_transition,
    assert_step_transition,
    module_can_transition,
    step_can_transition,
)


def test_step_allowed_chain():
    assert step_can_transition(StepStatus.NOT_STARTED, StepStatus.IN_PROGRESS)
    assert step_can_transition(StepStatus.IN_PROGRESS, StepStatus.COMPLETE)
    assert step_can_transition(
        StepStatus.IN_PROGRESS, StepStatus.BACKEND_VALIDATION_FAILED
    )
    assert step_can_transition(StepStatus.COMPLETE, StepStatus.REVIEW_PENDING)


def test_step_illegal_jump_rejected():
    assert not step_can_transition(StepStatus.NOT_STARTED, StepStatus.COMPLETE)
    assert not step_can_transition(StepStatus.NOT_STARTED, StepStatus.COMPLETED)
    with pytest.raises(IllegalTransition):
        assert_step_transition(StepStatus.NOT_STARTED, StepStatus.COMPLETE)


def test_module_allowed_and_illegal():
    assert module_can_transition(ModuleStatus.LOCKED, ModuleStatus.AVAILABLE)
    assert module_can_transition(ModuleStatus.AVAILABLE, ModuleStatus.IN_PROGRESS)
    assert module_can_transition(
        ModuleStatus.IN_PROGRESS, ModuleStatus.WAITING_ZWEIPLUS
    )
    assert not module_can_transition(ModuleStatus.LOCKED, ModuleStatus.IN_PROGRESS)
    assert not module_can_transition(ModuleStatus.IMPORTED, ModuleStatus.AVAILABLE)
    with pytest.raises(IllegalTransition):
        assert_module_transition(ModuleStatus.LOCKED, ModuleStatus.COMPLETED)


def test_same_status_is_noop_allowed():
    assert step_can_transition(StepStatus.IN_PROGRESS, StepStatus.IN_PROGRESS)
    assert module_can_transition(ModuleStatus.LOCKED, ModuleStatus.LOCKED)
