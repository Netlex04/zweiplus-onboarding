"""Module engine: instance creation, initial unlocks, progress, follow-up unlock."""

import pytest

from app.models import ModuleDefinition, StepInstance
from app.models.enums import ModuleStatus, StepStatus
from app.seeds.loader import load_seeds
from app.services import module_engine


@pytest.fixture
def seeded(db_session):
    load_seeds(db_session)
    db_session.commit()
    return db_session


def _module_by_key(session, process, key):
    for m in process.modules:
        mdef = session.get(ModuleDefinition, m.module_def_id)
        if mdef.key == key:
            return m, mdef
    raise AssertionError(f"module {key} not found")


def test_create_process_initial_unlocks(seeded):
    process = module_engine.create_process_instance(
        seeded, process_def_key="datenschutz_basis_onboarding",
        customer_name="ACME GmbH",
    )
    seeded.commit()

    sw, _ = _module_by_key(seeded, process, "software_inventory")
    tom, _ = _module_by_key(seeded, process, "tom_erfassung")
    avv, _ = _module_by_key(seeded, process, "avv_onboarding")

    assert sw.status == ModuleStatus.AVAILABLE.value
    assert sw.unlocked is True
    assert tom.status == ModuleStatus.LOCKED.value
    assert avv.status == ModuleStatus.LOCKED.value

    # Steps materialised for every module.
    assert len(sw.steps) == 2  # basic_information + data_transfer


def test_progress_calculation(seeded):
    process = module_engine.create_process_instance(
        seeded, process_def_key="datenschutz_basis_onboarding",
        customer_name="ACME GmbH",
    )
    sw, _ = _module_by_key(seeded, process, "software_inventory")
    assert module_engine.module_progress(sw) == 0
    sw.steps[0].status = StepStatus.COMPLETE.value
    seeded.flush()
    assert module_engine.module_progress(sw) == 50
    sw.steps[1].status = StepStatus.COMPLETE.value
    seeded.flush()
    assert module_engine.module_progress(sw) == 100


def test_followup_unlock_after_completion(seeded):
    process = module_engine.create_process_instance(
        seeded, process_def_key="datenschutz_basis_onboarding",
        customer_name="ACME GmbH",
    )
    sw, _ = _module_by_key(seeded, process, "software_inventory")
    for step in sw.steps:
        step.status = StepStatus.COMPLETE.value
    seeded.flush()

    module_engine.evaluate_unlocks(seeded, process)
    seeded.flush()

    tom, _ = _module_by_key(seeded, process, "tom_erfassung")
    avv, _ = _module_by_key(seeded, process, "avv_onboarding")
    assert tom.status == ModuleStatus.AVAILABLE.value
    assert avv.status == ModuleStatus.AVAILABLE.value
    assert tom.unlocked and avv.unlocked


def test_visibility_rule(seeded):
    process = module_engine.create_process_instance(
        seeded, process_def_key="datenschutz_basis_onboarding",
        customer_name="ACME GmbH",
    )
    sw, _ = _module_by_key(seeded, process, "software_inventory")
    data_transfer = [
        s for s in sw.steps
        if seeded.get(StepInstance, s.id)
    ]
    # Find the data_transfer step and its third_country_details question.
    from app.models import QuestionDefinition, StepDefinition

    step = next(
        s for s in sw.steps
        if seeded.get(StepDefinition, s.step_def_id).key == "data_transfer"
    )
    sdef = seeded.get(StepDefinition, step.step_def_id)
    details_q = next(
        q for q in module_engine.question_def_by_step(seeded, sdef.id)
        if q.key == "third_country_details"
    )
    assert not module_engine.is_question_visible(details_q, {"third_country": "nein"})
    assert module_engine.is_question_visible(details_q, {"third_country": "ja"})
