"""Backend validation: positive + negative cases (FR-VAL)."""

import pytest

from app.models import ModuleDefinition, StepDefinition
from app.models.enums import StepStatus
from app.seeds.loader import load_seeds
from app.services import module_engine, step_service, validation
from app.services.step_service import StepNotEditable


@pytest.fixture
def basic_step(db_session):
    load_seeds(db_session)
    db_session.commit()
    process = module_engine.create_process_instance(
        db_session, process_def_key="datenschutz_basis_onboarding",
        customer_name="ACME GmbH",
    )
    db_session.commit()
    sw = next(
        m for m in process.modules
        if db_session.get(ModuleDefinition, m.module_def_id).key == "software_inventory"
    )
    step = next(
        s for s in sw.steps
        if db_session.get(StepDefinition, s.step_def_id).key == "basic_information"
    )
    return db_session, step


def test_required_field_missing(basic_step):
    session, step = basic_step
    outcome = validation.validate_step(session, step)
    assert outcome.passed is False
    codes = {e["code"] for e in outcome.errors}
    assert "required" in codes  # used_software is required


def test_valid_answers_pass(basic_step):
    session, step = basic_step
    step_service.save_answers(
        session, step,
        [{"question_key": "used_software", "value": ["DATEV"]}],
        created_by="kunde@demo.test",
    )
    session.flush()
    outcome = validation.validate_step(session, step)
    assert outcome.passed is True
    assert outcome.errors == []


def test_invalid_select_value(basic_step):
    session, step = basic_step
    step_service.save_answers(
        session, step,
        [{"question_key": "used_software", "value": ["NichtInListe"]}],
        created_by="kunde@demo.test",
    )
    session.flush()
    outcome = validation.validate_step(session, step)
    assert outcome.passed is False
    assert any(e["code"] == "invalid_option" for e in outcome.errors)


def test_type_error(basic_step):
    session, step = basic_step
    # multi_select expects a list; give a string -> type error
    step_service.save_answers(
        session, step,
        [{"question_key": "used_software", "value": "DATEV"}],
        created_by="kunde@demo.test",
    )
    session.flush()
    outcome = validation.validate_step(session, step)
    assert any(e["code"] == "type" for e in outcome.errors)


def test_complete_gate(basic_step):
    session, step = basic_step
    # Without answers -> cannot complete
    with pytest.raises(StepNotEditable):
        step_service.complete_step(session, step)
    assert step.status == StepStatus.BACKEND_VALIDATION_FAILED.value

    # With valid answers -> completes
    step_service.save_answers(
        session, step,
        [{"question_key": "used_software", "value": ["DATEV"]}],
        created_by="kunde@demo.test",
    )
    session.flush()
    step_service.complete_step(session, step)
    assert step.status == StepStatus.COMPLETE.value


def test_hidden_required_not_enforced(db_session):
    """third_country_details is hidden unless third_country == 'ja'."""
    load_seeds(db_session)
    db_session.commit()
    process = module_engine.create_process_instance(
        db_session, process_def_key="datenschutz_basis_onboarding",
        customer_name="ACME GmbH",
    )
    db_session.commit()
    sw = next(
        m for m in process.modules
        if db_session.get(ModuleDefinition, m.module_def_id).key == "software_inventory"
    )
    dt = next(
        s for s in sw.steps
        if db_session.get(StepDefinition, s.step_def_id).key == "data_transfer"
    )
    # third_country is required; answer 'nein' -> details hidden, step valid.
    step_service.save_answers(
        db_session, dt,
        [{"question_key": "third_country", "value": "nein"}],
        created_by="kunde@demo.test",
    )
    db_session.flush()
    outcome = validation.validate_step(db_session, dt)
    assert outcome.passed is True
