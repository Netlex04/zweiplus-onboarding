"""Prompt-composition unit tests: knowledge cascade + data minimisation."""

from __future__ import annotations

import pytest

from sqlalchemy import select

from app.models import (
    ModuleDefinition,
    ModuleInstance,
    QuestionDefinition,
    StepDefinition,
)
from app.seeds.loader import load_seeds
from app.services.ai_context import build_system_prompt, gather_answer_context
from app.services.module_engine import (
    create_process_instance,
    question_def_by_step,
)


@pytest.fixture
def seeded(db_session):
    load_seeds(db_session)
    db_session.commit()
    return db_session


def _software_module_def(session) -> ModuleDefinition:
    return session.scalar(
        select(ModuleDefinition).where(ModuleDefinition.key == "software_inventory")
    )


def test_question_prompt_contains_cascaded_knowledge_contents(seeded):
    session = seeded
    module_def = _software_module_def(session)
    step_def = session.scalar(
        select(StepDefinition).where(
            StepDefinition.module_def_id == module_def.id,
            StepDefinition.key == "basic_information",
        )
    )
    question = session.scalar(
        select(QuestionDefinition).where(
            QuestionDefinition.step_def_id == step_def.id,
            QuestionDefinition.key == "used_software",
        )
    )

    prompt = build_system_prompt(
        session,
        context="question",
        module=module_def,
        step=step_def,
        question=question,
    )

    # Module-level knowledge content (not just the key) is present.
    assert "Auftragsverarbeiter" in prompt  # processor_definitions content
    assert "weisungsgebunden" in prompt
    # Question knowledge_scope content present.
    assert "personenbezogene Daten" in prompt
    # Deduplicated: processor_definitions appears once (module + question scope).
    assert prompt.count("Auftragsverarbeiter – Begriff") == 1


def test_step_prompt_includes_step_knowledge(seeded):
    session = seeded
    module_def = _software_module_def(session)
    step_def = session.scalar(
        select(StepDefinition).where(
            StepDefinition.module_def_id == module_def.id,
            StepDefinition.key == "data_transfer",
        )
    )
    prompt = build_system_prompt(
        session, context="step", module=module_def, step=step_def
    )
    # Step-level config references third_country_transfer_basics.
    assert "Drittlandübermittlung" in prompt


def test_dashboard_prompt_has_no_module_knowledge(seeded):
    session = seeded
    prompt = build_system_prompt(session, context="dashboard")
    assert "orientier" in prompt.lower()
    # No module-specific knowledge content.
    assert "Auftragsverarbeiter" not in prompt
    assert "Drittlandübermittlung" not in prompt


def test_gather_answer_context_minimises_data(seeded):
    session = seeded
    # Create a real process + answer some questions.
    process = create_process_instance(
        session,
        process_def_key="datenschutz_basis_onboarding",
        customer_name="Demo Kunde",
    )
    session.flush()
    module = session.scalars(
        select(ModuleInstance).where(
            ModuleInstance.process_instance_id == process.id
        )
    ).first()
    module_def = session.get(ModuleDefinition, module.module_def_id)
    # Find the basic_information step instance.
    from app.models import Answer

    step_inst = None
    for s in module.steps:
        sd = session.get(StepDefinition, s.step_def_id)
        if sd.key == "basic_information":
            step_inst = s
            break
    assert step_inst is not None
    q = next(
        qq
        for qq in question_def_by_step(session, step_inst.step_def_id)
        if qq.key == "used_software"
    )
    session.add(
        Answer(
            step_instance_id=step_inst.id,
            question_def_id=q.id,
            value=["Microsoft 365"],
            created_by="kunde@demo.test",
        )
    )
    session.flush()

    summary = gather_answer_context(session, step=step_inst)
    assert "Microsoft 365" in summary
    # Data minimisation: no internal IDs / hashes / secrets.
    assert step_inst.id not in summary
    assert "password" not in summary.lower()
    assert "hash" not in summary.lower()
