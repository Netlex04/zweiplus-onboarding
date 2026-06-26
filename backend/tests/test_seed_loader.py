"""Seed loader: correct content + idempotency (Annahme A8/A9)."""

from sqlalchemy import func, select

from app.models import (
    KnowledgeEntry,
    ModuleDefinition,
    ProcessDefinition,
    QuestionDefinition,
    StepDefinition,
    TemplateDefinition,
    User,
)
from app.models.enums import QuestionType
from app.security import verify_password
from app.seeds.loader import load_seeds


def _count(session, model) -> int:
    return session.scalar(select(func.count()).select_from(model))


def test_seed_loads_expected_content(db_session):
    counts = load_seeds(db_session)
    db_session.commit()

    assert counts["process_definitions"] == 1
    assert counts["module_definitions"] == 3
    assert counts["users"] == 3

    process = db_session.scalar(
        select(ProcessDefinition).where(
            ProcessDefinition.key == "datenschutz_basis_onboarding"
        )
    )
    assert process is not None

    module_keys = set(
        db_session.scalars(select(ModuleDefinition.key)).all()
    )
    assert module_keys == {"software_inventory", "tom_erfassung", "avv_onboarding"}


def test_unlock_rules_match_annahme_a3(db_session):
    load_seeds(db_session)
    db_session.commit()
    by_key = {
        m.key: m for m in db_session.scalars(select(ModuleDefinition)).all()
    }
    assert by_key["software_inventory"].unlock_rule == {"type": "always"}
    assert by_key["tom_erfassung"].unlock_rule == {
        "type": "after",
        "requires": ["software_inventory"],
    }
    assert by_key["avv_onboarding"].unlock_rule == {
        "type": "after",
        "requires": ["software_inventory"],
    }


def test_all_four_question_types_present(db_session):
    load_seeds(db_session)
    db_session.commit()
    types = set(db_session.scalars(select(QuestionDefinition.type)).all())
    assert {
        QuestionType.SINGLE_SELECT.value,
        QuestionType.MULTI_SELECT.value,
        QuestionType.TEXT.value,
        QuestionType.FILE_UPLOAD.value,
    } <= types


def test_visibility_rule_present(db_session):
    load_seeds(db_session)
    db_session.commit()
    q = db_session.scalar(
        select(QuestionDefinition).where(
            QuestionDefinition.key == "third_country_details"
        )
    )
    assert q.visibility_rule == {"questionKey": "third_country", "equals": "ja"}


def test_knowledge_entries_cover_referenced_keys(db_session):
    load_seeds(db_session)
    db_session.commit()

    known = set(db_session.scalars(select(KnowledgeEntry.key)).all())
    referenced: set[str] = set()
    for module in db_session.scalars(select(ModuleDefinition)).all():
        cfg = module.ai_knowledge_config or {}
        for values in cfg.values():
            referenced.update(values)
    for step in db_session.scalars(select(StepDefinition)).all():
        cfg = step.ai_knowledge_config or {}
        for values in cfg.values():
            referenced.update(values)
    for question in db_session.scalars(select(QuestionDefinition)).all():
        referenced.update(question.knowledge_scope or [])

    missing = referenced - known
    assert not missing, f"KnowledgeEntry fehlt für: {sorted(missing)}"


def test_templates_seeded(db_session):
    load_seeds(db_session)
    db_session.commit()
    keys = set(db_session.scalars(select(TemplateDefinition.key)).all())
    assert {"software_vendor_email", "software_vendor_questionnaire"} <= keys
    email_tpl = db_session.scalar(
        select(TemplateDefinition).where(
            TemplateDefinition.key == "software_vendor_email"
        )
    )
    assert email_tpl.type == "email"
    assert email_tpl.scope == "step"


def test_demo_users_hashed_and_verifiable(db_session):
    load_seeds(db_session)
    db_session.commit()
    user = db_session.scalar(select(User).where(User.email == "kunde@demo.test"))
    assert user.role == "customer"
    assert user.password_hash != "demo1234"  # stored hashed
    assert verify_password("demo1234", user.password_hash)
    assert not verify_password("wrong", user.password_hash)


def test_seed_loader_is_idempotent(db_session):
    load_seeds(db_session)
    db_session.commit()
    first = {
        m.__name__: _count(db_session, m)
        for m in (
            ProcessDefinition,
            ModuleDefinition,
            StepDefinition,
            QuestionDefinition,
            TemplateDefinition,
            KnowledgeEntry,
            User,
        )
    }

    load_seeds(db_session)
    db_session.commit()
    second = {
        m.__name__: _count(db_session, m)
        for m in (
            ProcessDefinition,
            ModuleDefinition,
            StepDefinition,
            QuestionDefinition,
            TemplateDefinition,
            KnowledgeEntry,
            User,
        )
    }

    assert first == second, f"Duplikate beim 2. Lauf: {first} -> {second}"
